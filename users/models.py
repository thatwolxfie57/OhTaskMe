from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import pytz

class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    
    Adds timezone field for proper task scheduling based on user's location.
    
    TODO: Add UserProfile relationship for role, industry, experience level
    TODO: Add UserPreferences for task generation preferences and work patterns
    TODO: Implement user behavior tracking for adaptive AI suggestions
    TODO: Add productivity pattern analysis and optimization features
    TODO: Integrate with machine learning models for personalized recommendations
    """
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        help_text=_('Select your timezone for accurate task scheduling.')
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.username


# TODO: Implement UserProfile model for Phase 2 - User-Centric Intelligence
"""
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=[
        ('student', 'Student'),
        ('professional', 'Professional'),
        ('manager', 'Manager'),
        ('entrepreneur', 'Entrepreneur'),
        ('healthcare', 'Healthcare Worker'),
        ('teacher', 'Teacher/Educator'),
        ('other', 'Other')
    ], default='other')
    industry = models.CharField(max_length=100, blank=True)
    experience_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert')
    ], default='intermediate')
    work_style = models.CharField(max_length=20, choices=[
        ('detailed', 'Detailed Planning'),
        ('minimal', 'Minimal Planning'),
        ('collaborative', 'Collaborative'),
        ('independent', 'Independent')
    ], default='detailed')
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
"""

# TODO: Implement UserPreferences model for Phase 2
"""
class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    preferred_prep_time = models.IntegerField(default=3, help_text="Days before event to start preparation")
    task_detail_level = models.CharField(max_length=20, choices=[
        ('minimal', 'Minimal Details'),
        ('standard', 'Standard Details'),
        ('detailed', 'Detailed Tasks')
    ], default='standard')
    reminder_frequency = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    work_hours_start = models.TimeField(default='09:00')
    work_hours_end = models.TimeField(default='17:00')
    
    def __str__(self):
        return f"{self.user.username} preferences"
"""

# TODO: Implement TaskFeedback model for Phase 3 - Machine Learning
"""
class TaskFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50)
    suggested_task = models.TextField()
    accepted = models.BooleanField()
    completed = models.BooleanField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    user_rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback: {self.user.username} - {self.event_title}"
"""
