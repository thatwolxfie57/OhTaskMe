from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, date
import json

User = get_user_model()


class UserStatistics(models.Model):
    """
    Track comprehensive user performance metrics and productivity statistics.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='statistics')
    
    # XP and Level System
    total_xp = models.IntegerField(default=0, help_text="Total experience points earned")
    current_level = models.IntegerField(default=1, help_text="Current user level")
    xp_to_next_level = models.IntegerField(default=100, help_text="XP needed for next level")
    
    # Task Statistics
    total_tasks_created = models.IntegerField(default=0)
    total_tasks_completed = models.IntegerField(default=0)
    total_tasks_overdue = models.IntegerField(default=0)
    
    # Streak Tracking
    current_daily_streak = models.IntegerField(default=0, help_text="Current consecutive days with completed tasks")
    longest_daily_streak = models.IntegerField(default=0, help_text="Longest streak ever achieved")
    current_weekly_streak = models.IntegerField(default=0, help_text="Current consecutive weeks with goals met")
    longest_weekly_streak = models.IntegerField(default=0)
    
    # Time Tracking
    total_time_saved = models.IntegerField(default=0, help_text="Total minutes saved through task completion")
    average_completion_time = models.FloatField(default=0.0, help_text="Average task completion time in hours")
    
    # Productivity Metrics
    productivity_score = models.FloatField(default=0.0, help_text="Overall productivity score (0-100)")
    completion_rate = models.FloatField(default=0.0, help_text="Task completion percentage")
    punctuality_score = models.FloatField(default=100.0, help_text="On-time completion percentage")
    
    # Mental Health Indicators
    stress_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('critical', 'Critical')
        ],
        default='low'
    )
    work_life_balance_score = models.FloatField(default=75.0, help_text="Work-life balance score (0-100)")
    burnout_risk = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Risk'),
            ('moderate', 'Moderate Risk'),
            ('high', 'High Risk'),
            ('critical', 'Critical Risk')
        ],
        default='low'
    )
    
    # Last updated
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Statistics"
        verbose_name_plural = "User Statistics"
    
    def __str__(self):
        return f"{self.user.username} - Level {self.current_level} ({self.total_xp} XP)"
    
    def add_xp(self, points, reason=""):
        """Add XP to user with proper logging and level checking."""
        self.total_xp += points
        self._check_level_up()
        
        # Create XP log entry
        XPLog.objects.create(
            user_statistics=self,
            points_earned=points,
            reason=reason
        )
        self.save()
    
    def remove_xp(self, points, reason=""):
        """Remove XP from user (for task incompletion, etc.)."""
        self.total_xp = max(0, self.total_xp - points)
        
        # Create negative XP log entry
        XPLog.objects.create(
            user_statistics=self,
            points_earned=-points,
            reason=f"Removed: {reason}"
        )
        self.save()
    
    def _check_level_up(self):
        """Check if user should level up and handle progression."""
        while self.total_xp >= self.xp_to_next_level:
            self.current_level += 1
            # Exponential XP requirement growth
            self.xp_to_next_level = int(100 * (1.5 ** (self.current_level - 1)))
            
            # Create achievement for level up
            AchievementBadge.objects.get_or_create(
                user_statistics=self,
                badge_type='level',
                title=f'Level {self.current_level} Achieved!',
                description=f'Reached level {self.current_level}',
                defaults={'unlocked_at': timezone.now()}
            )
    
    def update_completion_rate(self):
        """Recalculate completion rate based on current tasks."""
        if self.total_tasks_created > 0:
            self.completion_rate = (self.total_tasks_completed / self.total_tasks_created) * 100
        else:
            self.completion_rate = 0.0
        self.save()
    
    def calculate_productivity_score(self):
        """Calculate overall productivity score based on multiple factors."""
        factors = {
            'completion_rate': self.completion_rate * 0.4,  # 40% weight
            'punctuality_score': self.punctuality_score * 0.3,  # 30% weight
            'streak_bonus': min(self.current_daily_streak * 2, 20),  # Up to 20 points
            'consistency_bonus': min(self.current_weekly_streak * 1, 10)  # Up to 10 points
        }
        
        self.productivity_score = min(sum(factors.values()), 100.0)
        self.save()
        return self.productivity_score
    
    @property
    def xp_remaining_to_next_level(self):
        """Calculate XP remaining to reach the next level."""
        return max(self.xp_to_next_level - self.total_xp, 0)


class DailyStats(models.Model):
    """
    Track daily productivity metrics for trend analysis and progress monitoring.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()
    
    # Daily Metrics
    tasks_created = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    tasks_overdue = models.IntegerField(default=0)
    events_attended = models.IntegerField(default=0)
    
    # Time Tracking
    total_work_time = models.IntegerField(default=0, help_text="Total minutes worked")
    focus_time = models.IntegerField(default=0, help_text="Deep focus time in minutes")
    break_time = models.IntegerField(default=0, help_text="Break time in minutes")
    
    # Productivity Metrics
    daily_productivity_score = models.FloatField(default=0.0)
    mood_rating = models.IntegerField(
        default=5,
        choices=[(i, str(i)) for i in range(1, 11)],
        help_text="Daily mood rating (1-10)"
    )
    energy_level = models.IntegerField(
        default=5,
        choices=[(i, str(i)) for i in range(1, 11)],
        help_text="Energy level (1-10)"
    )
    
    # Goals
    daily_goal_set = models.BooleanField(default=False)
    daily_goal_achieved = models.BooleanField(default=False)
    daily_goal_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name = "Daily Statistics"
        verbose_name_plural = "Daily Statistics"
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    @classmethod
    def get_or_create_today(cls, user):
        """Get or create today's daily stats for a user."""
        today = timezone.now().date()
        daily_stats, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'daily_productivity_score': 0.0,
                'mood_rating': 5,
                'energy_level': 5
            }
        )
        return daily_stats


class AchievementBadge(models.Model):
    """
    Gamification system for tracking user achievements and milestones.
    """
    BADGE_TYPES = [
        ('first_task', 'First Task'),
        ('first_week', 'First Week'),
        ('perfect_day', 'Perfect Day'),
        ('perfect_week', 'Perfect Week'),
        ('perfect_month', 'Perfect Month'),
        ('early_bird', 'Early Bird'),
        ('night_owl', 'Night Owl'),
        ('streak_master', 'Streak Master'),
        ('productivity_guru', 'Productivity Guru'),
        ('level', 'Level Achievement'),
        ('time_saver', 'Time Saver'),
        ('event_master', 'Event Master'),
        ('consistency_king', 'Consistency King'),
        ('overachiever', 'Overachiever'),
        ('wellness_warrior', 'Wellness Warrior'),
        ('habit_builder', 'Habit Builder'),
        ('goal_getter', 'Goal Getter'),
        ('custom', 'Custom Achievement')
    ]
    
    user_statistics = models.ForeignKey(UserStatistics, on_delete=models.CASCADE, related_name='achievements')
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-trophy', help_text="FontAwesome icon class")
    color = models.CharField(max_length=20, default='gold', help_text="Badge color")
    
    # Metadata
    unlocked_at = models.DateTimeField()
    is_rare = models.BooleanField(default=False, help_text="Rare achievements are harder to obtain")
    rarity_level = models.CharField(
        max_length=20,
        choices=[
            ('common', 'Common'),
            ('rare', 'Rare'),
            ('epic', 'Epic'),
            ('legendary', 'Legendary')
        ],
        default='common'
    )
    
    class Meta:
        unique_together = ['user_statistics', 'badge_type', 'title']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user_statistics.user.username} - {self.title}"


class StreakTracking(models.Model):
    """
    Detailed tracking of user streaks for motivation and habit formation.
    """
    STREAK_TYPES = [
        ('daily_tasks', 'Daily Task Completion'),
        ('weekly_goals', 'Weekly Goal Achievement'),
        ('monthly_targets', 'Monthly Target Achievement'),
        ('perfect_days', 'Perfect Days'),
        ('early_completions', 'Early Task Completions'),
        ('habit_21day', '21-Day Habit Challenge'),
        ('custom', 'Custom Streak')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streaks')
    streak_type = models.CharField(max_length=50, choices=STREAK_TYPES)
    current_count = models.IntegerField(default=0)
    best_count = models.IntegerField(default=0)
    last_updated = models.DateField()
    
    # Streak Details
    streak_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_count = models.IntegerField(null=True, blank=True, help_text="Target streak length")
    is_active = models.BooleanField(default=True)
    
    # Rewards
    milestone_rewards = models.JSONField(default=dict, help_text="Milestone rewards configuration")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'streak_type', 'streak_name']
        ordering = ['-current_count']
    
    def __str__(self):
        return f"{self.user.username} - {self.streak_name}: {self.current_count}"
    
    def increment_streak(self):
        """Increment the streak and check for milestone rewards."""
        self.current_count += 1
        if self.current_count > self.best_count:
            self.best_count = self.current_count
            
        self.last_updated = timezone.now().date()
        self.save()
        
        # Check for milestone rewards
        self._check_milestone_rewards()
    
    def break_streak(self):
        """Reset the current streak count."""
        self.current_count = 0
        self.last_updated = timezone.now().date()
        self.save()
    
    def is_active_today(self):
        """Check if the streak was already updated today."""
        today = timezone.now().date()
        return self.last_updated == today
    
    def _check_milestone_rewards(self):
        """Check if user has reached any milestone rewards."""
        milestones = self.milestone_rewards.get('milestones', [])
        for milestone in milestones:
            if self.current_count == milestone.get('count', 0):
                # Award milestone XP
                user_stats = UserStatistics.objects.get(user=self.user)
                user_stats.add_xp(
                    milestone.get('xp_reward', 50),
                    f"Streak milestone: {milestone.get('name', 'Unnamed')}"
                )
                
                # Create achievement if specified
                if milestone.get('create_achievement', False):
                    AchievementBadge.objects.get_or_create(
                        user_statistics=user_stats,
                        badge_type='streak_master',
                        title=milestone.get('achievement_title', f'{self.streak_name} Milestone'),
                        description=milestone.get('achievement_description', f'Reached {self.current_count} day streak'),
                        defaults={'unlocked_at': timezone.now()}
                    )


class UserGoals(models.Model):
    """
    Track user-defined goals and their progress for motivation and habit formation.
    """
    GOAL_TYPES = [
        ('daily', 'Daily Goal'),
        ('weekly', 'Weekly Goal'),
        ('monthly', 'Monthly Goal'),
        ('habit_21day', '21-Day Habit'),
        ('custom', 'Custom Goal')
    ]
    
    GOAL_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('failed', 'Failed'),
        ('archived', 'Archived')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Progress Tracking
    target_value = models.IntegerField(help_text="Target number to achieve")
    current_progress = models.IntegerField(default=0)
    progress_unit = models.CharField(max_length=50, default="tasks", help_text="Unit of measurement")
    
    # Dates
    start_date = models.DateField()
    target_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=GOAL_STATUS, default='active')
    is_public = models.BooleanField(default=False, help_text="Share goal with other users")
    
    # Rewards
    reward_xp = models.IntegerField(default=100, help_text="XP reward for completion")
    custom_reward = models.CharField(max_length=200, blank=True, help_text="Personal reward description")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @property
    def progress_percentage(self):
        """Calculate progress as a percentage."""
        if self.target_value > 0:
            return min((self.current_progress / self.target_value) * 100, 100)
        return 0
    
    @property
    def days_remaining(self):
        """Calculate days remaining to achieve the goal."""
        if self.status == 'completed':
            return 0
        today = timezone.now().date()
        return max((self.target_date - today).days, 0)
    
    def update_progress(self, increment=1):
        """Update goal progress and check for completion."""
        self.current_progress += increment
        
        if self.current_progress >= self.target_value:
            self.mark_completed()
        
        self.save()
    
    def mark_completed(self):
        """Mark goal as completed and award rewards."""
        self.status = 'completed'
        self.completed_date = timezone.now().date()
        
        # Award XP
        user_stats, created = UserStatistics.objects.get_or_create(user=self.user)
        user_stats.add_xp(self.reward_xp, f"Goal completed: {self.title}")
        
        # Create achievement
        AchievementBadge.objects.get_or_create(
            user_statistics=user_stats,
            badge_type='goal_getter',
            title=f'Goal Achieved: {self.title}',
            description=f'Successfully completed the goal: {self.title}',
            defaults={'unlocked_at': timezone.now()}
        )
        
        self.save()


class XPLog(models.Model):
    """
    Log all XP transactions for transparency and gamification feedback.
    """
    user_statistics = models.ForeignKey(UserStatistics, on_delete=models.CASCADE, related_name='xp_logs')
    points_earned = models.IntegerField()
    reason = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional references
    related_task_id = models.IntegerField(null=True, blank=True)
    related_event_id = models.IntegerField(null=True, blank=True)
    related_goal_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user_statistics.user.username} - {self.points_earned} XP - {self.reason}"


class ProductivityInsights(models.Model):
    """
    Store AI-generated insights and recommendations for user productivity improvement.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(
        max_length=50,
        choices=[
            ('productivity_tip', 'Productivity Tip'),
            ('pattern_analysis', 'Pattern Analysis'),
            ('time_optimization', 'Time Optimization'),
            ('stress_reduction', 'Stress Reduction'),
            ('habit_suggestion', 'Habit Suggestion'),
            ('achievement_opportunity', 'Achievement Opportunity')
        ]
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    confidence_score = models.FloatField(help_text="AI confidence in this insight (0-1)")
    
    # Metadata
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        default='medium'
    )
    
    # Actions
    action_taken = models.BooleanField(default=False)
    action_description = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
