"""
Serializers for the statistics application.
Defines the structure for API responses and data validation.
"""

from rest_framework import serializers
from .models import (
    UserStatistics, DailyStats, AchievementBadge, 
    StreakTracking, UserGoals, XPLog, ProductivityInsights
)


class UserStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for UserStatistics model."""
    xp_to_next_level = serializers.ReadOnlyField()
    xp_remaining_to_next_level = serializers.ReadOnlyField()
    completion_rate = serializers.ReadOnlyField()
    productivity_score = serializers.ReadOnlyField()
    
    class Meta:
        model = UserStatistics
        fields = [
            'total_xp', 'current_level', 'xp_to_next_level', 'xp_remaining_to_next_level',
            'tasks_completed', 'tasks_created', 'completion_rate',
            'events_attended', 'events_created', 'productivity_score',
            'last_active', 'streak_count', 'best_streak'
        ]


class DailyStatsSerializer(serializers.ModelSerializer):
    """Serializer for DailyStats model."""
    
    class Meta:
        model = DailyStats
        fields = [
            'date', 'tasks_completed', 'tasks_created', 'events_attended',
            'events_created', 'productivity_score', 'mood_rating', 'notes'
        ]


class AchievementBadgeSerializer(serializers.ModelSerializer):
    """Serializer for AchievementBadge model."""
    badge_type_display = serializers.CharField(source='get_badge_type_display', read_only=True)
    rarity_display = serializers.CharField(source='get_rarity_display', read_only=True)
    
    class Meta:
        model = AchievementBadge
        fields = [
            'badge_type', 'badge_type_display', 'title', 'description',
            'rarity', 'rarity_display', 'icon', 'earned_date'
        ]


class StreakTrackingSerializer(serializers.ModelSerializer):
    """Serializer for StreakTracking model."""
    
    class Meta:
        model = StreakTracking
        fields = [
            'streak_type', 'current_count', 'best_count', 'last_updated',
            'is_active', 'target_count'
        ]


class UserGoalsSerializer(serializers.ModelSerializer):
    """Serializer for UserGoals model."""
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = UserGoals
        fields = [
            'goal_type', 'title', 'description', 'target_value', 'current_value',
            'progress_percentage', 'start_date', 'target_date', 'days_remaining',
            'is_completed', 'completed_date'
        ]


class XPLogSerializer(serializers.ModelSerializer):
    """Serializer for XPLog model."""
    
    class Meta:
        model = XPLog
        fields = ['points_earned', 'reason', 'earned_date']


class ProductivityInsightsSerializer(serializers.ModelSerializer):
    """Serializer for ProductivityInsights model."""
    
    class Meta:
        model = ProductivityInsights
        fields = [
            'insight_type', 'title', 'description', 'recommendation',
            'confidence_score', 'generated_date', 'is_dismissed'
        ]


class StatisticsDashboardSerializer(serializers.Serializer):
    """Comprehensive serializer for dashboard data."""
    user_statistics = UserStatisticsSerializer()
    recent_achievements = AchievementBadgeSerializer(many=True)
    active_streaks = StreakTrackingSerializer(many=True)
    current_goals = UserGoalsSerializer(many=True)
    recent_insights = ProductivityInsightsSerializer(many=True)
    daily_stats = DailyStatsSerializer(many=True)


class StatisticsAPIResponseSerializer(serializers.Serializer):
    """Serializer for statistics API responses."""
    type = serializers.CharField()
    data = serializers.ListField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_records = serializers.IntegerField()
