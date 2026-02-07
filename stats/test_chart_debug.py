"""
Debug script to test chart data generation directly
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ohtaskme.settings')
django.setup()

from users.models import User
from stats.models import UserStatistics, DailyStats, XPLog
from stats.views import _get_real_time_analytics
from datetime import datetime, timedelta

def test_chart_data_generation():
    """Test the chart data generation process"""
    
    # Get admin user
    admin = User.objects.get(username='admin')
    print(f"Testing chart data for user: {admin.username}")
    
    # Get user statistics
    user_stats, created = UserStatistics.objects.get_or_create(user=admin)
    print(f"User stats: XP={user_stats.total_xp}, Level={user_stats.current_level}")
    
    # Get date range (last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get daily stats
    daily_stats = DailyStats.objects.filter(
        user=admin,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    print(f"Daily stats found: {daily_stats.count()}")
    for stat in daily_stats:
        print(f"  {stat.date}: {stat.tasks_completed} tasks, {stat.daily_productivity_score} score")
    
    # Get recent XP logs
    recent_xp_logs = XPLog.objects.filter(
        user_statistics__user=admin
    ).order_by('-timestamp')[:30]
    
    print(f"XP logs found: {recent_xp_logs.count()}")
    for log in recent_xp_logs[:5]:  # Show first 5
        print(f"  {log.timestamp}: +{log.points_earned} XP - {log.reason}")
    
    # Real-time analytics data
    print("\nGenerating real-time analytics...")
    real_time_data = _get_real_time_analytics(admin)
    
    productivity_trend = real_time_data['productivity_patterns']['productivity_trend']
    print(f"Productivity trend entries: {len(productivity_trend)}")
    for entry in productivity_trend[:3]:  # Show first 3
        print(f"  {entry}")
    
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
        ],
        'user_stats': {
            'total_xp': user_stats.total_xp,
            'current_level': user_stats.current_level,
            'xp_to_next_level': user_stats.xp_to_next_level,
        }
    }
    
    # Use real-time productivity trend if available
    if productivity_trend:
        print("Using real-time productivity trend")
        chart_data['daily_productivity'] = productivity_trend
    
    # Add fallback data if empty
    if not chart_data['daily_productivity']:
        print("Adding fallback productivity data")
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
        print("Adding fallback XP progression data")
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
    
    print(f"\nFinal chart data:")
    print(f"Daily productivity entries: {len(chart_data['daily_productivity'])}")
    print(f"XP progression entries: {len(chart_data['xp_progression'])}")
    
    print(f"\nFirst productivity entry: {chart_data['daily_productivity'][0] if chart_data['daily_productivity'] else 'None'}")
    print(f"First XP entry: {chart_data['xp_progression'][0] if chart_data['xp_progression'] else 'None'}")
    
    # Test JSON serialization
    try:
        json_data = json.dumps(chart_data, indent=2)
        print(f"\nJSON serialization successful, length: {len(json_data)} chars")
        return chart_data
    except Exception as e:
        print(f"JSON serialization failed: {e}")
        return None

if __name__ == "__main__":
    test_chart_data_generation()
