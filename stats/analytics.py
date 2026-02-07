"""
Real-time Productivity Analytics View

This view provides users with live insights into their productivity patterns,
helping them understand their habits and make intentional improvements.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
from datetime import datetime, timedelta
import json

from .models import (
    UserStatistics, DailyStats, StreakTracking, 
    ProductivityInsights, AchievementBadge, XPLog
)
from tasks.models import Task

@login_required
def real_time_analytics(request):
    """
    Real-time productivity analytics dashboard showing live insights
    into user behavior patterns and productivity trends.
    """
    user = request.user
    
    # Get or create user statistics
    user_stats, _ = UserStatistics.objects.get_or_create(user=user)
    
    # Calculate real-time metrics
    analytics_data = {
        'user_stats': user_stats,
        'current_insights': _get_current_insights(user),
        'productivity_patterns': _get_productivity_patterns(user),
        'streak_status': _get_streak_status(user),
        'achievement_progress': _get_achievement_progress(user),
        'time_analysis': _get_time_analysis(user),
        'goal_tracking': _get_goal_tracking(user),
        'habit_insights': _get_habit_insights(user),
        'weekly_report': _get_weekly_report(user)
    }
    
    return render(request, 'stats/real_time_analytics.html', analytics_data)

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
    insights['achievements_today'] = AchievementBadge.objects.filter(
        user=user,
        unlocked_at__date=today
    ).values_list('title', flat=True)
    
    # Streaks at risk (haven't been updated today)
    insights['streaks_at_risk'] = StreakTracking.objects.filter(
        user=user,
        is_active=True,
        last_updated__lt=today,
        current_count__gt=0
    ).values_list('streak_name', flat=True)
    
    return insights