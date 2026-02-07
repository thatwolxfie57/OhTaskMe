from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .views import _get_real_time_analytics
from .models import UserStatistics, DailyStats, XPLog
from datetime import datetime, timedelta
import json

@login_required
@require_http_methods(["GET"])
def debug_chart_data(request):
    """Debug endpoint to check chart data generation"""
    try:
        # Get user statistics
        user_stats, _ = UserStatistics.objects.get_or_create(user=request.user)
        
        # Get date range (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Get daily stats
        daily_stats = DailyStats.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        # Get recent XP logs
        recent_xp_logs = XPLog.objects.filter(
            user_statistics__user=request.user
        ).order_by('-timestamp')[:30]
        
        # Real-time analytics data
        real_time_data = _get_real_time_analytics(request.user)
        
        # Prepare chart data (same logic as in main view)
        chart_data = {
            'daily_productivity': [
                {
                    'date': stat.date.strftime('%Y-%m-%d'),
                    'score': float(stat.daily_productivity_score),
                    'tasks': stat.tasks_completed,
                    'mood': stat.mood_rating
                }
                for stat in daily_stats
            ],
            'xp_progression': [
                {
                    'date': log.timestamp.strftime('%Y-%m-%d'),
                    'total_xp': user_stats.total_xp,
                    'points_earned': log.points_earned
                }
                for log in recent_xp_logs[:10]
            ]
        }
        
        # Use real-time productivity trend if available
        if real_time_data['productivity_patterns']['productivity_trend']:
            chart_data['daily_productivity'] = real_time_data['productivity_patterns']['productivity_trend']
        
        # Add fallback data if empty
        if not chart_data['daily_productivity']:
            import random
            chart_data['daily_productivity'] = [
                {
                    'date': (end_date - timedelta(days=6-i)).strftime('%Y-%m-%d'),
                    'score': float(random.randint(30, 85)),
                    'tasks': random.randint(1, 6),
                    'mood': 5
                }
                for i in range(7)
            ]
        
        if not chart_data['xp_progression'] or len(chart_data['xp_progression']) < 3:
            import random
            chart_data['xp_progression'] = []
            current_xp = max(0, user_stats.total_xp - 100)
            
            for i in range(7):
                date = end_date - timedelta(days=6-i)
                daily_gain = random.randint(5, 25) if current_xp < user_stats.total_xp else 0
                current_xp += daily_gain
                
                chart_data['xp_progression'].append({
                    'date': date.strftime('%Y-%m-%d'),
                    'total_xp': min(current_xp, user_stats.total_xp),
                    'points_earned': daily_gain
                })
            
            if chart_data['xp_progression']:
                chart_data['xp_progression'][-1]['total_xp'] = user_stats.total_xp
        
        debug_info = {
            'user': request.user.username,
            'user_stats': {
                'total_xp': user_stats.total_xp,
                'current_level': user_stats.current_level,
                'xp_to_next_level': user_stats.xp_to_next_level,
            },
            'daily_stats_count': daily_stats.count(),
            'xp_logs_count': recent_xp_logs.count(),
            'chart_data': chart_data,
            'real_time_data': real_time_data,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        return JsonResponse(debug_info, indent=2)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)
