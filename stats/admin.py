from django.contrib import admin
from .models import (
    UserStatistics, DailyStats, AchievementBadge, 
    StreakTracking, UserGoals, XPLog, ProductivityInsights
)


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_level', 'total_xp', 'completion_rate', 'productivity_score', 'current_daily_streak']
    list_filter = ['current_level', 'stress_level', 'burnout_risk']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'last_updated']
    
    fieldsets = [
        ('User Info', {
            'fields': ['user']
        }),
        ('XP & Level System', {
            'fields': ['total_xp', 'current_level', 'xp_to_next_level']
        }),
        ('Task Statistics', {
            'fields': ['total_tasks_created', 'total_tasks_completed', 'total_tasks_overdue']
        }),
        ('Streaks', {
            'fields': ['current_daily_streak', 'longest_daily_streak', 'current_weekly_streak', 'longest_weekly_streak']
        }),
        ('Productivity Metrics', {
            'fields': ['productivity_score', 'completion_rate', 'punctuality_score']
        }),
        ('Mental Health', {
            'fields': ['stress_level', 'work_life_balance_score', 'burnout_risk']
        }),
        ('Time Tracking', {
            'fields': ['total_time_saved', 'average_completion_time']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'last_updated']
        })
    ]


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'tasks_completed', 'daily_productivity_score', 'mood_rating', 'energy_level']
    list_filter = ['date', 'mood_rating', 'energy_level', 'daily_goal_achieved']
    search_fields = ['user__username']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(AchievementBadge)
class AchievementBadgeAdmin(admin.ModelAdmin):
    list_display = ['user_statistics', 'title', 'badge_type', 'rarity_level', 'unlocked_at']
    list_filter = ['badge_type', 'rarity_level', 'is_rare', 'unlocked_at']
    search_fields = ['user_statistics__user__username', 'title', 'description']
    readonly_fields = ['unlocked_at']
    date_hierarchy = 'unlocked_at'


@admin.register(StreakTracking)
class StreakTrackingAdmin(admin.ModelAdmin):
    list_display = ['user', 'streak_name', 'streak_type', 'current_count', 'best_count', 'is_active']
    list_filter = ['streak_type', 'is_active', 'last_updated']
    search_fields = ['user__username', 'streak_name']
    readonly_fields = ['created_at']


@admin.register(UserGoals)
class UserGoalsAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'goal_type', 'progress_percentage', 'status', 'target_date']
    list_filter = ['goal_type', 'status', 'start_date', 'target_date']
    search_fields = ['user__username', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage', 'days_remaining']
    date_hierarchy = 'target_date'
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage.short_description = "Progress"


@admin.register(XPLog)
class XPLogAdmin(admin.ModelAdmin):
    list_display = ['user_statistics', 'points_earned', 'reason', 'timestamp']
    list_filter = ['timestamp', 'points_earned']
    search_fields = ['user_statistics__user__username', 'reason']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(ProductivityInsights)
class ProductivityInsightsAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'insight_type', 'priority', 'confidence_score', 'is_read', 'created_at']
    list_filter = ['insight_type', 'priority', 'is_read', 'is_dismissed', 'action_taken', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
