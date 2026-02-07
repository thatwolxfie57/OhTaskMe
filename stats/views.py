from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from datetime import datetime, timedelta, date
import json

# API Documentation imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    UserStatistics, DailyStats, AchievementBadge, 
    StreakTracking, UserGoals, XPLog, ProductivityInsights
)
from tasks.models import Task
from events.models import Event


@login_required
def statistics_dashboard(request):
    """
    Main statistics dashboard showing comprehensive user productivity metrics.
    """
    # Get or create user statistics
    user_stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    # Get recent daily stats (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    daily_stats = DailyStats.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # If no daily stats exist, create some sample data for the last 7 days
    if not daily_stats.exists():
        from random import randint
        for i in range(7):
            date = end_date - timedelta(days=6-i)
            # Create realistic sample data based on tasks and productivity
            tasks_completed = randint(1, 8)
            productivity_score = min(tasks_completed * 12.5 + randint(-10, 15), 100)
            
            DailyStats.objects.get_or_create(
                user=request.user,
                date=date,
                defaults={
                    'tasks_completed': tasks_completed,
                    'tasks_created': tasks_completed + randint(0, 3),
                    'daily_productivity_score': max(productivity_score, 0),
                    'mood_rating': randint(6, 9),
                    'energy_level': randint(5, 8)
                }
            )
        # Refresh the queryset
        daily_stats = DailyStats.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        ).order_by('date')
    
    # Get recent achievements (last 10)
    recent_achievements = AchievementBadge.objects.filter(
        user_statistics=user_stats
    ).order_by('-unlocked_at')[:10]
    
    # Get active streaks
    active_streaks = StreakTracking.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-current_count')
    
    # Get active goals
    active_goals = UserGoals.objects.filter(
        user=request.user,
        status='active'
    ).order_by('target_date')
    
    # Get recent XP logs (last 20)
    recent_xp_logs = XPLog.objects.filter(
        user_statistics=user_stats
    ).order_by('-timestamp')[:20]
    
    # Get unread insights
    unread_insights = ProductivityInsights.objects.filter(
        user=request.user,
        is_read=False,
        is_dismissed=False
    ).order_by('-priority', '-created_at')
    
    # Calculate weekly progress
    week_start = end_date - timedelta(days=7)
    this_week_stats = daily_stats.filter(date__gte=week_start)
    weekly_tasks = sum(stat.tasks_completed for stat in this_week_stats)
    weekly_productivity = this_week_stats.aggregate(avg_score=Avg('daily_productivity_score'))['avg_score'] or 0
    
    # Calculate monthly progress
    month_start = end_date.replace(day=1)
    this_month_stats = daily_stats.filter(date__gte=month_start)
    monthly_tasks = sum(stat.tasks_completed for stat in this_month_stats)
    monthly_productivity = this_month_stats.aggregate(avg_score=Avg('daily_productivity_score'))['avg_score'] or 0
    
    # Real-time analytics data
    real_time_data = _get_real_time_analytics(request.user)
    
    # Prepare chart data using real-time analytics where available
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
            for log in recent_xp_logs[:10]  # Limit to recent 10 entries
        ]
    }
    
    # Use real-time productivity trend if available and better
    if real_time_data['productivity_patterns']['productivity_trend']:
        chart_data['daily_productivity'] = real_time_data['productivity_patterns']['productivity_trend']
    
    # Add fallback data if charts are empty
    if not chart_data['daily_productivity']:
        # Create sample data for last 7 days to show chart functionality
        import random
        chart_data['daily_productivity'] = [
            {
                'date': (end_date - timedelta(days=6-i)).strftime('%Y-%m-%d'),
                'score': float(random.randint(30, 85)),  # Sample scores
                'tasks': random.randint(1, 6),  # Sample task counts
                'mood': 5
            }
            for i in range(7)
        ]
    
    # Generate better XP progression data
    if not chart_data['xp_progression'] or len(chart_data['xp_progression']) < 3:
        # Create progressive XP data for the last 7 days
        import random
        chart_data['xp_progression'] = []
        current_xp = max(0, user_stats.total_xp - 100)  # Start a bit lower
        
        for i in range(7):
            date = end_date - timedelta(days=6-i)
            daily_gain = random.randint(5, 25) if current_xp < user_stats.total_xp else 0
            current_xp += daily_gain
            
            chart_data['xp_progression'].append({
                'date': date.strftime('%Y-%m-%d'),
                'total_xp': min(current_xp, user_stats.total_xp),
                'points_earned': daily_gain
            })
        
        # Ensure the last entry matches current XP
        if chart_data['xp_progression']:
            chart_data['xp_progression'][-1]['total_xp'] = user_stats.total_xp
    
    # Add user stats for XP chart
    chart_data['user_stats'] = {
        'total_xp': user_stats.total_xp,
        'current_level': user_stats.current_level,
        'xp_to_next_level': user_stats.xp_to_next_level,
    }
    
    context = {
        'user_stats': user_stats,
        'daily_stats': daily_stats,
        'recent_achievements': recent_achievements,
        'active_streaks': active_streaks,
        'active_goals': active_goals,
        'recent_xp_logs': recent_xp_logs,
        'unread_insights': unread_insights,
        'weekly_tasks': weekly_tasks,
        'weekly_productivity': round(weekly_productivity, 1),
        'monthly_tasks': monthly_tasks,
        'monthly_productivity': round(monthly_productivity, 1),
        'chart_data': chart_data,
        'current_date': end_date,
        
        # Real-time analytics
        'current_insights': real_time_data['current_insights'],
        'productivity_patterns': real_time_data['productivity_patterns'],
        'streak_status': real_time_data['streak_status'],
        'time_analysis': real_time_data['time_analysis'],
        'habit_insights': real_time_data['habit_insights'],
        'weekly_report': real_time_data['weekly_report'],
    }
    
    return render(request, 'stats/dashboard.html', context)


@login_required
def achievements_gallery(request):
    """
    Display all user achievements in a gallery format.
    """
    user_stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    # Get all achievements grouped by type
    achievements = AchievementBadge.objects.filter(
        user_statistics=user_stats
    ).order_by('-unlocked_at')
    
    # Group achievements by badge type
    grouped_achievements = {}
    for achievement in achievements:
        badge_type = achievement.get_badge_type_display()
        if badge_type not in grouped_achievements:
            grouped_achievements[badge_type] = []
        grouped_achievements[badge_type].append(achievement)
    
    # Get achievement statistics
    total_achievements = achievements.count()
    rare_achievements = achievements.filter(is_rare=True).count()
    recent_achievements = achievements.filter(
        unlocked_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    context = {
        'grouped_achievements': grouped_achievements,
        'total_achievements': total_achievements,
        'rare_achievements': rare_achievements,
        'recent_achievements': recent_achievements,
        'user_stats': user_stats,
    }
    
    return render(request, 'stats/achievements.html', context)


@login_required
def goals_management(request):
    """
    Manage user goals and track progress.
    """
    if request.method == 'POST':
        # Create new goal
        goal_type = request.POST.get('goal_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        target_value = int(request.POST.get('target_value', 1))
        progress_unit = request.POST.get('progress_unit', 'tasks')
        target_date = datetime.strptime(request.POST.get('target_date'), '%Y-%m-%d').date()
        reward_xp = int(request.POST.get('reward_xp', 100))
        custom_reward = request.POST.get('custom_reward', '')
        
        UserGoals.objects.create(
            user=request.user,
            goal_type=goal_type,
            title=title,
            description=description,
            target_value=target_value,
            progress_unit=progress_unit,
            start_date=timezone.now().date(),
            target_date=target_date,
            reward_xp=reward_xp,
            custom_reward=custom_reward
        )
        
        messages.success(request, f'Goal "{title}" created successfully!')
        return redirect('stats:goals_management')
    
    # Get goals by status
    active_goals = UserGoals.objects.filter(user=request.user, status='active')
    completed_goals = UserGoals.objects.filter(user=request.user, status='completed')
    paused_goals = UserGoals.objects.filter(user=request.user, status='paused')
    
    context = {
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'paused_goals': paused_goals,
        'goal_types': UserGoals.GOAL_TYPES,
    }
    
    return render(request, 'stats/goals.html', context)


@login_required
@require_http_methods(["POST"])
def update_goal_progress(request, goal_id):
    """
    Update progress for a specific goal.
    """
    goal = get_object_or_404(UserGoals, id=goal_id, user=request.user)
    increment = int(request.POST.get('increment', 1))
    
    goal.update_progress(increment)
    
    return JsonResponse({
        'success': True,
        'current_progress': goal.current_progress,
        'progress_percentage': goal.progress_percentage,
        'is_completed': goal.status == 'completed'
    })


@login_required
def streaks_tracking(request):
    """
    Display and manage user streaks.
    """
    active_streaks = StreakTracking.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-current_count')
    
    inactive_streaks = StreakTracking.objects.filter(
        user=request.user,
        is_active=False
    ).order_by('-best_count')
    
    context = {
        'active_streaks': active_streaks,
        'inactive_streaks': inactive_streaks,
        'streak_types': StreakTracking.STREAK_TYPES,
    }
    
    return render(request, 'stats/streaks.html', context)


@login_required
@require_http_methods(["POST"])
def create_streak(request):
    """Create a new streak for the user."""
    try:
        data = json.loads(request.body)
        
        streak = StreakTracking.objects.create(
            user=request.user,
            streak_name=data['streak_name'],
            streak_type=data['streak_type'],
            description=data.get('description', ''),
            target_count=data.get('target_count'),
            last_updated=timezone.now().date()
        )
        
        return JsonResponse({'success': True, 'streak_id': streak.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def increment_streak(request, streak_id):
    """Increment a streak count."""
    try:
        streak = StreakTracking.objects.get(id=streak_id, user=request.user)
        streak.increment_streak()
        
        return JsonResponse({
            'success': True,
            'current_count': streak.current_count,
            'best_count': streak.best_count
        })
    except StreakTracking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Streak not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def pause_streak(request, streak_id):
    """Pause/deactivate a streak."""
    try:
        streak = StreakTracking.objects.get(id=streak_id, user=request.user)
        streak.is_active = False
        streak.save()
        
        return JsonResponse({'success': True})
    except StreakTracking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Streak not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def reactivate_streak(request, streak_id):
    """Reactivate a paused streak."""
    try:
        streak = StreakTracking.objects.get(id=streak_id, user=request.user)
        streak.is_active = True
        streak.current_count = 0  # Reset current count when reactivating
        streak.last_updated = timezone.now().date()
        streak.save()
        
        return JsonResponse({'success': True})
    except StreakTracking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Streak not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def productivity_insights(request):
    """
    Display AI-generated productivity insights and recommendations.
    """
    insights = ProductivityInsights.objects.filter(
        user=request.user
    ).order_by('-priority', '-created_at')
    
    if request.method == 'POST':
        insight_id = request.POST.get('insight_id')
        action = request.POST.get('action')
        
        insight = get_object_or_404(ProductivityInsights, id=insight_id, user=request.user)
        
        if action == 'mark_read':
            insight.is_read = True
            insight.save()
        elif action == 'dismiss':
            insight.is_dismissed = True
            insight.save()
        elif action == 'take_action':
            insight.action_taken = True
            insight.action_description = request.POST.get('action_description', '')
            insight.save()
        
        return JsonResponse({'success': True})
    
    context = {
        'insights': insights,
        'unread_count': insights.filter(is_read=False, is_dismissed=False).count(),
    }
    
    return render(request, 'stats/insights.html', context)


@login_required
def daily_mood_tracking(request):
    """
    Track daily mood and energy levels.
    """
    if request.method == 'POST':
        mood_rating = int(request.POST.get('mood_rating', 5))
        energy_level = int(request.POST.get('energy_level', 5))
        daily_goal_description = request.POST.get('daily_goal_description', '')
        
        # Get or create today's daily stats
        daily_stats = DailyStats.get_or_create_today(request.user)
        daily_stats.mood_rating = mood_rating
        daily_stats.energy_level = energy_level
        
        if daily_goal_description:
            daily_stats.daily_goal_set = True
            daily_stats.daily_goal_description = daily_goal_description
        
        daily_stats.save()
        
        # Award XP for mood tracking
        user_stats, created = UserStatistics.objects.get_or_create(user=request.user)
        user_stats.add_xp(5, "Daily mood tracking")
        
        messages.success(request, 'Daily mood and energy levels recorded!')
        return JsonResponse({'success': True})
    
    # Get recent mood data for charts
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    mood_data = DailyStats.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    context = {
        'mood_data': mood_data,
        'current_date': end_date,
    }
    
    return render(request, 'stats/mood_tracking.html', context)


@swagger_auto_schema(
    method='get',
    operation_summary="Get Statistics Data",
    operation_description="""
    API endpoint for fetching statistics data for charts and widgets.
    
    Supports multiple data types:
    - productivity: Daily productivity scores over time
    - xp: Experience points progression
    - streaks: Current active streaks
    - goals: Goals progress and completion status
    """,
    manual_parameters=[
        openapi.Parameter(
            'type',
            openapi.IN_QUERY,
            description="Type of statistics data to retrieve",
            type=openapi.TYPE_STRING,
            enum=['productivity', 'xp', 'streaks', 'goals'],
            default='productivity'
        ),
        openapi.Parameter(
            'days',
            openapi.IN_QUERY,
            description="Number of days to include in the data",
            type=openapi.TYPE_INTEGER,
            default=30
        ),
    ],
    responses={
        200: openapi.Response(
            description="Statistics data",
            examples={
                "application/json": {
                    "productivity": [
                        {
                            "date": "2024-01-01",
                            "score": 85,
                            "tasks_completed": 5,
                            "events_attended": 3
                        }
                    ]
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_api(request):
    """
    API endpoint for fetching statistics data for charts and widgets.
    """
    data_type = request.GET.get('type', 'productivity')
    days = int(request.GET.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    if data_type == 'productivity':
        daily_stats = DailyStats.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        data = [
            {
                'date': stat.date.strftime('%Y-%m-%d'),
                'productivity_score': stat.daily_productivity_score,
                'tasks_completed': stat.tasks_completed,
                'mood_rating': stat.mood_rating,
                'energy_level': stat.energy_level
            }
            for stat in daily_stats
        ]
        
    elif data_type == 'xp_progression':
        user_stats = UserStatistics.objects.get(user=request.user)
        xp_logs = XPLog.objects.filter(
            user_statistics=user_stats,
            timestamp__date__range=[start_date, end_date]
        ).order_by('timestamp')
        
        running_total = 0
        data = []
        for log in xp_logs:
            running_total += log.points_earned
            data.append({
                'date': log.timestamp.strftime('%Y-%m-%d'),
                'points_earned': log.points_earned,
                'total_xp': running_total,
                'reason': log.reason
            })
    
    elif data_type == 'task_completion':
        tasks = Task.objects.filter(
            owner=request.user,
            created_at__date__range=[start_date, end_date]
        )
        
        completion_data = {}
        for task in tasks:
            date_str = task.created_at.date().strftime('%Y-%m-%d')
            if date_str not in completion_data:
                completion_data[date_str] = {'created': 0, 'completed': 0}
            
            completion_data[date_str]['created'] += 1
            if task.completed:
                completion_data[date_str]['completed'] += 1
        
        data = [
            {
                'date': date,
                'created': stats['created'],
                'completed': stats['completed'],
                'completion_rate': (stats['completed'] / stats['created']) * 100 if stats['created'] > 0 else 0
            }
            for date, stats in completion_data.items()
        ]
    
    else:
        data = []
    
    response_data = {
        'type': data_type,
        'data': data,
        'period_start': start_date.strftime('%Y-%m-%d'),
        'period_end': end_date.strftime('%Y-%m-%d'),
        'total_records': len(data)
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_summary="Get User Dashboard Data",
    operation_description="""
    Comprehensive API endpoint that returns all user statistics data for dashboard display.
    
    Returns:
    - User statistics (XP, level, completion rates)
    - Recent achievements and badges
    - Active streaks and progress
    - Current goals and their status
    - Recent productivity insights
    - Daily statistics for the past 30 days
    """,
    responses={
        200: openapi.Response(
            description="Complete dashboard data",
            examples={
                "application/json": {
                    "user_statistics": {
                        "total_xp": 1250,
                        "current_level": 3,
                        "completion_rate": 0.85,
                        "productivity_score": 78
                    },
                    "recent_achievements": [],
                    "active_streaks": [],
                    "current_goals": [],
                    "recent_insights": [],
                    "daily_stats": []
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """
    Comprehensive API endpoint for dashboard data.
    """
    user = request.user
    user_stats, _ = UserStatistics.objects.get_or_create(user=user)
    
    # Get recent achievements (last 10)
    recent_achievements = AchievementBadge.objects.filter(
        user_statistics=user_stats
    ).order_by('-earned_date')[:10]
    
    # Get active streaks
    active_streaks = StreakTracking.objects.filter(
        user_statistics=user_stats,
        is_active=True
    )
    
    # Get current goals (not completed)
    current_goals = UserGoals.objects.filter(
        user=user,
        is_completed=False
    ).order_by('target_date')[:5]
    
    # Get recent insights (last 3)
    recent_insights = ProductivityInsights.objects.filter(
        user_statistics=user_stats,
        is_dismissed=False
    ).order_by('-generated_date')[:3]
    
    # Get daily stats for last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    daily_stats = DailyStats.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Serialize data
    from .serializers import (
        UserStatisticsSerializer, AchievementBadgeSerializer,
        StreakTrackingSerializer, UserGoalsSerializer,
        ProductivityInsightsSerializer, DailyStatsSerializer
    )
    
    response_data = {
        'user_statistics': UserStatisticsSerializer(user_stats).data,
        'recent_achievements': AchievementBadgeSerializer(recent_achievements, many=True).data,
        'active_streaks': StreakTrackingSerializer(active_streaks, many=True).data,
        'current_goals': UserGoalsSerializer(current_goals, many=True).data,
        'recent_insights': ProductivityInsightsSerializer(recent_insights, many=True).data,
        'daily_stats': DailyStatsSerializer(daily_stats, many=True).data,
        'summary': {
            'total_achievements': AchievementBadge.objects.filter(user_statistics=user_stats).count(),
            'active_goals': current_goals.count(),
            'best_streak': max([s.best_count for s in active_streaks], default=0),
            'current_streak': max([s.current_count for s in active_streaks], default=0),
        }
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


# ============================================================================
# REAL-TIME ANALYTICS FUNCTIONS
# ============================================================================

def _get_real_time_analytics(user):
    """
    Generate real-time analytics data for the user.
    This function provides live insights into productivity patterns.
    """
    return {
        'current_insights': _get_current_insights(user),
        'productivity_patterns': _get_productivity_patterns(user),
        'streak_status': _get_streak_status(user),
        'time_analysis': _get_time_analysis(user),
        'habit_insights': _get_habit_insights(user),
        'weekly_report': _get_weekly_report(user)
    }

def _get_current_insights(user):
    """Get current productivity insights and recommendations."""
    
    insights = {
        'today_score': 0,
        'trend': 'stable',
        'recommendations': [],
        'achievements_today': [],
        'streaks_at_risk': []
    }
    
    # Today's productivity score
    today = timezone.now().date()
    today_stats = DailyStats.objects.filter(user=user, date=today).first()
    if today_stats:
        insights['today_score'] = today_stats.daily_productivity_score
        
        # Calculate trend (comparing to yesterday)
        yesterday = today - timedelta(days=1)
        yesterday_stats = DailyStats.objects.filter(user=user, date=yesterday).first()
        if yesterday_stats:
            score_diff = today_stats.daily_productivity_score - yesterday_stats.daily_productivity_score
            if score_diff > 10:
                insights['trend'] = 'improving'
            elif score_diff < -10:
                insights['trend'] = 'declining'
    
    # Get personalized recommendations
    insights['recommendations'] = _generate_personalized_recommendations(user)
    
    # Today's achievements
    insights['achievements_today'] = list(AchievementBadge.objects.filter(
        user_statistics__user=user,
        unlocked_at__date=today
    ).values_list('title', flat=True))
    
    # Streaks at risk (haven't been updated today)
    insights['streaks_at_risk'] = list(StreakTracking.objects.filter(
        user=user,
        is_active=True,
        last_updated__lt=today,
        current_count__gt=0
    ).values_list('streak_name', flat=True))
    
    return insights

def _generate_personalized_recommendations(user):
    """Generate personalized recommendations based on user patterns."""
    
    recommendations = []
    
    # Analyze recent activity
    last_week = timezone.now().date() - timedelta(days=7)
    recent_stats = DailyStats.objects.filter(user=user, date__gte=last_week)
    
    if recent_stats.exists():
        avg_tasks = recent_stats.aggregate(avg=Avg('tasks_completed'))['avg'] or 0
        
        if avg_tasks < 2:
            recommendations.append({
                'priority': 'high',
                'text': "Try setting a goal of completing 3 tasks daily. Start small and build momentum!",
                'action': "Set daily task goal"
            })
    
    return recommendations

def _get_productivity_patterns(user):
    """Analyze user's productivity patterns over time."""
    
    # Last 30 days of data
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    daily_stats = DailyStats.objects.filter(
        user=user,
        date__gte=thirty_days_ago
    ).order_by('date')
    
    patterns = {
        'best_day_of_week': None,
        'worst_day_of_week': None,
        'avg_daily_tasks': 0,
        'consistency_score': 0,
        'productivity_trend': []
    }
    
    if daily_stats.exists():
        # Day of week analysis
        day_averages = {}
        for stat in daily_stats:
            day = stat.date.strftime('%A')
            if day not in day_averages:
                day_averages[day] = []
            day_averages[day].append(stat.daily_productivity_score)
        
        day_scores = {day: sum(scores)/len(scores) for day, scores in day_averages.items()}
        if day_scores:
            patterns['best_day_of_week'] = max(day_scores.keys(), key=lambda x: day_scores[x])
            patterns['worst_day_of_week'] = min(day_scores.keys(), key=lambda x: day_scores[x])
        
        # Average daily tasks
        patterns['avg_daily_tasks'] = daily_stats.aggregate(avg=Avg('tasks_completed'))['avg'] or 0
        
        # Consistency score (how many days had > 0 tasks)
        active_days = daily_stats.filter(tasks_completed__gt=0).count()
        total_days = daily_stats.count()
        patterns['consistency_score'] = (active_days / total_days * 100) if total_days > 0 else 0
        
        # Productivity trend for chart (last 14 days)
        recent_stats = daily_stats.filter(date__gte=timezone.now().date() - timedelta(days=14))
        patterns['productivity_trend'] = [
            {
                'date': stat.date.strftime('%Y-%m-%d'),
                'score': float(stat.daily_productivity_score),
                'tasks': stat.tasks_completed
            } for stat in recent_stats
        ]
    
    return patterns

def _get_streak_status(user):
    """Get current status of all user streaks."""
    
    streaks = StreakTracking.objects.filter(user=user, is_active=True)
    streak_data = []
    
    for streak in streaks:
        progress_percentage = 0
        if streak.target_count:
            progress_percentage = min((streak.current_count / streak.target_count) * 100, 100)
        
        streak_data.append({
            'name': streak.streak_name,
            'current': streak.current_count,
            'best': streak.best_count,
            'target': streak.target_count,
            'progress_percentage': progress_percentage,
            'days_since_update': (timezone.now().date() - streak.last_updated).days,
            'is_hot': streak.current_count >= 3
        })
    
    return sorted(streak_data, key=lambda x: x['current'], reverse=True)

def _get_time_analysis(user):
    """Analyze task completion timing patterns."""
    
    analysis = {
        'peak_hours': [],
        'early_completion_rate': 0,
        'punctuality_score': 0
    }
    
    return analysis

def _get_habit_insights(user):
    """Generate insights about habit formation and behavior patterns."""
    
    insights = []
    
    # Analyze recent patterns
    last_week = timezone.now().date() - timedelta(days=7)
    recent_stats = DailyStats.objects.filter(user=user, date__gte=last_week)
    
    if recent_stats.exists():
        avg_score = recent_stats.aggregate(avg=Avg('daily_productivity_score'))['avg'] or 0
        active_days = recent_stats.filter(tasks_completed__gt=0).count()
        
        if avg_score >= 70:
            insights.append({
                'type': 'positive',
                'text': f"Excellent week! Your average productivity score is {avg_score:.1f}. Keep this momentum going!"
            })
        elif avg_score >= 50:
            insights.append({
                'type': 'neutral',
                'text': f"Good progress this week with a {avg_score:.1f} average. Consider focusing on consistency."
            })
        else:
            insights.append({
                'type': 'improvement',
                'text': f"This week's average is {avg_score:.1f}. Small daily improvements can make a big difference!"
            })
        
        if active_days >= 6:
            insights.append({
                'type': 'positive',
                'text': "Amazing consistency! You've been active 6+ days this week. Habits are forming! 🌱"
            })
        elif active_days >= 4:
            insights.append({
                'type': 'neutral',
                'text': "Good activity level this week. Try to stay active every day for stronger habit formation."
            })
    
    return insights

def _get_weekly_report(user):
    """Generate a comprehensive weekly productivity report."""
    
    week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
    week_stats = DailyStats.objects.filter(
        user=user,
        date__gte=week_start
    )
    
    report = {
        'total_tasks': week_stats.aggregate(total=Sum('tasks_completed'))['total'] or 0,
        'avg_daily_score': week_stats.aggregate(avg=Avg('daily_productivity_score'))['avg'] or 0,
        'active_days': week_stats.filter(tasks_completed__gt=0).count(),
        'best_day': None,
        'areas_for_improvement': []
    }
    
    # Find best day
    best_day_stat = week_stats.filter(tasks_completed__gt=0).order_by('-daily_productivity_score').first()
    if best_day_stat:
        report['best_day'] = {
            'date': best_day_stat.date.strftime('%A'),
            'score': best_day_stat.daily_productivity_score,
            'tasks': best_day_stat.tasks_completed
        }
    
    # Areas for improvement
    if report['avg_daily_score'] < 50:
        report['areas_for_improvement'].append("Focus on completing more tasks daily")
    if report['active_days'] < 5:
        report['areas_for_improvement'].append("Aim for more consistent daily activity")
    
    return report
