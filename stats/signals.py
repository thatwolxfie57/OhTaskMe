"""
Real-time Statistics Tracking System

This module contains Django signals that automatically track user behavior and update
productivity statistics in real-time. The system is designed to encourage intentional
living and productivity while being mathematically sound and meaningful.

Key Principles:
1. Real-time tracking based on actual user actions
2. Mathematically sound calculations
3. Focused on helping users live intentionally
4. Rewards productive behavior patterns
5. Provides insights for habit building
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta, time
import logging

from tasks.models import Task
from events.models import Event
from .models import (
    UserStatistics, DailyStats, StreakTracking, 
    XPLog, ProductivityInsights, AchievementBadge
)

logger = logging.getLogger(__name__)

# ============================================================================
# TASK COMPLETION TRACKING
# ============================================================================

@receiver(post_save, sender=Task)
def track_task_completion(sender, instance, created, **kwargs):
    """
    Track task completion and update real-time statistics.
    
    This signal fires whenever a task is saved and calculates:
    - Daily task completion counts
    - Productivity scores based on completion patterns
    - XP rewards for different types of completions
    - Streak tracking for consistent behavior
    """
    if not instance.owner:
        return
    
    try:
        # Get or create today's stats
        today = timezone.now().date()
        daily_stats, _ = DailyStats.objects.get_or_create(
            user=instance.owner,
            date=today,
            defaults={
                'daily_productivity_score': 0.0,
                'tasks_completed': 0,
                'tasks_overdue': 0,
            }
        )
        
        # Get or create user statistics
        user_stats, _ = UserStatistics.objects.get_or_create(user=instance.owner)
        
        # If task was just completed (not created as completed)
        if instance.completed and not created:
            _handle_task_completion(instance, daily_stats, user_stats)
            
        # If task was marked incomplete
        elif not instance.completed and not created:
            _handle_task_incompletion(instance, daily_stats, user_stats)
            
        # Update productivity score based on current task state
        _update_daily_productivity_score(daily_stats)
        
    except Exception as e:
        logger.error(f"Error in track_task_completion: {e}")

def _handle_task_completion(task, daily_stats, user_stats):
    """Handle when a task is marked as completed."""
    
    # Update daily stats
    daily_stats.tasks_completed += 1
    
    # Calculate completion timing for productivity insights
    now = timezone.now()
    completion_score = _calculate_completion_score(task, now)
    
    # Update user statistics
    user_stats.total_tasks_completed += 1
    
    # Calculate and award XP based on task characteristics
    xp_earned = _calculate_task_xp(task, completion_score)
    user_stats.add_xp(xp_earned, f"Completed: {task.description[:50]}")
    
    # Update streaks
    _update_task_completion_streaks(task.owner, daily_stats)
    
    # Save changes
    daily_stats.save()
    user_stats.save()
    
    # Generate insights for patterns
    _generate_completion_insights(task, completion_score)

def _handle_task_incompletion(task, daily_stats, user_stats):
    """Handle when a task is marked as incomplete."""
    
    # Only adjust if we had counted this completion today
    if daily_stats.tasks_completed > 0:
        daily_stats.tasks_completed -= 1
        user_stats.total_tasks_completed = max(0, user_stats.total_tasks_completed - 1)
        
        # Remove XP that was awarded (find the most recent XP log for this task)
        recent_xp = XPLog.objects.filter(
            user_statistics__user=task.owner,
            timestamp__date=timezone.now().date(),
            reason__icontains=task.description[:20]
        ).first()
        
        if recent_xp:
            user_stats.remove_xp(recent_xp.points_earned, f"Reverted: {task.description[:50]}")
            recent_xp.delete()
        
        daily_stats.save()
        user_stats.save()

def _calculate_completion_score(task, completion_time):
    """
    Calculate a productivity score based on task completion patterns.
    
    Factors considered:
    - Timeliness (completed before/after scheduled time)
    - Time of day (morning completion bonus)
    - Task age (completing older tasks gets bonus)
    - Consistency patterns
    
    Returns: float between 0.5 and 2.0 (multiplier for base XP)
    """
    score = 1.0
    
    # Timeliness bonus/penalty
    if task.scheduled_time:
        time_diff = completion_time - task.scheduled_time
        if time_diff.total_seconds() <= 0:  # Completed early or on time
            score += 0.3
        elif time_diff.days == 0:  # Same day but late
            score += 0.1
        elif time_diff.days <= 1:  # One day late
            score -= 0.1
        else:  # Multiple days late
            score -= 0.2
    
    # Morning completion bonus (before 10 AM)
    if completion_time.hour < 10:
        score += 0.2
    
    # Task age bonus (older tasks get higher scores)
    creation_age = completion_time - task.created_at
    if creation_age.days >= 7:
        score += 0.3
    elif creation_age.days >= 3:
        score += 0.1
    
    # Ensure score stays within reasonable bounds
    return max(0.5, min(2.0, score))

def _calculate_task_xp(task, completion_score):
    """
    Calculate XP reward for task completion.
    
    Base XP calculation:
    - Base: 10 XP per task
    - Scheduled vs unscheduled: +20% for scheduled
    - Event-related: +25% bonus
    - Description length (complexity indicator): +1 XP per 20 chars
    
    Final XP = base_xp * completion_score
    """
    base_xp = 10  # Base XP for any completed task
    
    # Scheduled task bonus
    if task.scheduled_time:
        base_xp = int(base_xp * 1.2)
    
    # Event-related task bonus
    if hasattr(task, 'event') and task.event:
        base_xp = int(base_xp * 1.25)
    
    # Complexity bonus based on description length
    complexity_bonus = len(task.description) // 20
    base_xp += complexity_bonus
    
    # Apply completion score multiplier
    final_xp = int(base_xp * completion_score)
    
    return max(5, final_xp)  # Minimum 5 XP per task

def _update_task_completion_streaks(user, daily_stats):
    """Update streak tracking for task completion patterns."""
    
    # Daily task completion streak
    task_streak, created = StreakTracking.objects.get_or_create(
        user=user,
        streak_type='daily_tasks',
        defaults={
            'current_count': 0,
            'target_count': 3,  # 3 tasks per day target
            'description': 'Complete at least 3 tasks daily'
        }
    )
    
    # Check if user hit their daily target
    if daily_stats.tasks_completed >= task_streak.target_count:
        if not task_streak.is_active_today():
            task_streak.increment_streak()

def _update_daily_productivity_score(daily_stats):
    """
    Calculate and update the daily productivity score.
    
    Score calculation:
    - Base: tasks_completed * 10 points
    - Overdue penalty: -5 points per overdue task
    - Time-based adjustments
    - Consistency bonuses
    
    Score range: 0-100
    """
    user = daily_stats.user
    
    # Base score from task completion
    base_score = daily_stats.tasks_completed * 10
    
    # Penalty for overdue tasks
    overdue_count = Task.objects.filter(
        owner=user,
        completed=False,
        scheduled_time__lt=timezone.now()
    ).count()
    
    daily_stats.tasks_overdue = overdue_count
    overdue_penalty = overdue_count * 5
    
    # Time-of-day bonus for early completions
    today_completions = Task.objects.filter(
        owner=user,
        completed=True,
        completed_at__date=timezone.now().date(),
        completed_at__hour__lt=12  # Completed before noon
    ).count()
    
    morning_bonus = today_completions * 3
    
    # Consistency bonus (completed tasks on consecutive days)
    consistency_bonus = _calculate_consistency_bonus(user)
    
    # Calculate final score
    raw_score = base_score - overdue_penalty + morning_bonus + consistency_bonus
    daily_stats.daily_productivity_score = max(0, min(100, raw_score))
    
    daily_stats.save()

def _calculate_consistency_bonus(user):
    """Calculate bonus points for consistent daily task completion."""
    
    # Look at last 7 days
    last_week = timezone.now().date() - timedelta(days=7)
    
    daily_completions = DailyStats.objects.filter(
        user=user,
        date__gte=last_week,
        tasks_completed__gte=1
    ).count()
    
    # Bonus points for consistent daily completion
    if daily_completions >= 7:
        return 15  # Perfect week
    elif daily_completions >= 5:
        return 10  # Good week
    elif daily_completions >= 3:
        return 5   # Decent consistency
    
    return 0

def _generate_completion_insights(task, completion_score):
    """Generate productivity insights based on completion patterns."""
    
    user = task.owner
    
    # Detect patterns and generate insights
    if completion_score >= 1.5:
        # High-productivity completion
        insight_text = f"Great job! You completed '{task.description[:30]}...' with excellent timing and efficiency."
        insight_type = "achievement"
        
    elif completion_score <= 0.7:
        # Room for improvement
        insight_text = f"Consider scheduling your tasks earlier to boost productivity. Task '{task.description[:30]}...' was completed late."
        insight_type = "suggestion"
        
    else:
        return  # No insight needed for average completion
    
    # Create insight if it doesn't exist recently
    recent_similar = ProductivityInsights.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(hours=2),
        insight_type=insight_type
    ).exists()
    
    if not recent_similar:
        ProductivityInsights.objects.create(
            user=user,
            insight_text=insight_text,
            insight_type=insight_type,
            is_read=False
        )

# ============================================================================
# EVENT ATTENDANCE TRACKING
# ============================================================================

@receiver(post_save, sender=Event)
def track_event_creation(sender, instance, created, **kwargs):
    """Track when users create events for planning insights."""
    
    if not created or not instance.owner:
        return
    
    try:
        user_stats, _ = UserStatistics.objects.get_or_create(user=instance.owner)
        
        # Small XP reward for planning ahead
        planning_xp = 5
        user_stats.add_xp(planning_xp, f"Created event: {instance.title[:30]}")
        
        # Update event planning streak
        _update_planning_streak(instance.owner)
        
    except Exception as e:
        logger.error(f"Error in track_event_creation: {e}")

def _update_planning_streak(user):
    """Update streak for consistent event planning."""
    
    planning_streak, created = StreakTracking.objects.get_or_create(
        user=user,
        streak_type='weekly_planning',
        defaults={
            'current_count': 0,
            'target_count': 1,  # Create at least 1 event per week
            'description': 'Plan ahead by creating events weekly'
        }
    )
    
    # Check if user created an event this week
    week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
    this_week_events = Event.objects.filter(
        owner=user,
        created_at__date__gte=week_start
    ).count()
    
    if this_week_events >= planning_streak.target_count:
        if not planning_streak.is_active_today():
            planning_streak.increment_streak()

# ============================================================================
# REAL-TIME PRODUCTIVITY MONITORING
# ============================================================================

@receiver(post_save, sender=DailyStats)
def monitor_daily_progress(sender, instance, created, **kwargs):
    """Monitor daily progress and provide real-time feedback."""
    
    if not created:  # Only run on updates
        _check_daily_milestones(instance)
        _update_weekly_patterns(instance)

def _check_daily_milestones(daily_stats):
    """Check if user hit important daily milestones."""
    
    user = daily_stats.user
    milestones = [
        (1, "First task completed today! 🎯"),
        (3, "Great momentum! 3 tasks completed! 🚀"),
        (5, "Productivity champion! 5 tasks done! 🏆"),
        (10, "Incredible! Double digits achieved! 🌟")
    ]
    
    for milestone_count, message in milestones:
        if daily_stats.tasks_completed == milestone_count:
            # Award milestone XP
            milestone_xp = milestone_count * 3
            user_stats, _ = UserStatistics.objects.get_or_create(user=user)
            user_stats.add_xp(milestone_xp, f"Daily milestone: {milestone_count} tasks")
            
            # Create achievement insight
            ProductivityInsights.objects.create(
                user=user,
                insight_text=message,
                insight_type="achievement",
                is_read=False
            )

def _update_weekly_patterns(daily_stats):
    """Analyze weekly patterns for insights."""
    
    user = daily_stats.user
    
    # Calculate weekly average
    week_start = timezone.now().date() - timedelta(days=7)
    weekly_stats = DailyStats.objects.filter(
        user=user,
        date__gte=week_start
    )
    
    if weekly_stats.count() >= 7:  # Full week of data
        avg_tasks = weekly_stats.aggregate(avg=Avg('tasks_completed'))['avg'] or 0
        avg_productivity = weekly_stats.aggregate(avg=Avg('daily_productivity_score'))['avg'] or 0
        
        # Detect trends
        if avg_tasks >= 5:
            insight = "You're consistently completing 5+ tasks daily! Excellent habit building! 🌱"
            ProductivityInsights.objects.get_or_create(
                user=user,
                insight_text=insight,
                insight_type="pattern",
                defaults={'is_read': False}
            )
        
        if avg_productivity >= 80:
            insight = "Your productivity score is consistently high! You're mastering intentional living! 🎯"
            ProductivityInsights.objects.get_or_create(
                user=user,
                insight_text=insight,
                insight_type="achievement",
                defaults={'is_read': False}
            )

# ============================================================================
# STREAK MONITORING & ACHIEVEMENTS
# ============================================================================

def check_and_award_achievements(user):
    """Check for achievement unlocks based on current statistics."""
    
    user_stats, _ = UserStatistics.objects.get_or_create(user=user)
    
    achievements = [
        # Task completion achievements
        ('first_task', 1, 'tasks', "First Step", "Completed your first task! 🎯"),
        ('task_novice', 10, 'tasks', "Task Novice", "Completed 10 tasks! Building momentum! 🚀"),
        ('task_adept', 50, 'tasks', "Task Adept", "50 tasks completed! You're getting good at this! 💪"),
        ('task_master', 100, 'tasks', "Task Master", "100 tasks! You're a productivity master! 🏆"),
        ('task_legend', 500, 'tasks', "Task Legend", "500 tasks! Legendary dedication! 🌟"),
        
        # XP achievements
        ('xp_beginner', 100, 'xp', "Getting Started", "Earned your first 100 XP! 🎮"),
        ('xp_rising', 500, 'xp', "Rising Star", "500 XP earned! You're rising! ⭐"),
        ('xp_champion', 1000, 'xp', "XP Champion", "1000 XP! True champion! 🏅"),
        ('xp_master', 5000, 'xp', "XP Master", "5000 XP! Mastery achieved! 👑"),
        
        # Streak achievements
        ('streak_starter', 3, 'streak', "Streak Starter", "3-day streak! Building habits! 🔥"),
        ('streak_builder', 7, 'streak', "Streak Builder", "Week-long streak! Consistency wins! 📈"),
        ('streak_master', 30, 'streak', "Streak Master", "30-day streak! Incredible discipline! 🏔️"),
    ]
    
    for achievement_id, threshold, stat_type, title, description in achievements:
        # Check if already earned
        if AchievementBadge.objects.filter(user_statistics=user_stats, badge_type=achievement_id).exists():
            continue
        
        # Check if threshold met
        earned = False
        if stat_type == 'tasks' and user_stats.total_tasks_completed >= threshold:
            earned = True
        elif stat_type == 'xp' and user_stats.total_xp >= threshold:
            earned = True
        elif stat_type == 'streak':
            max_streak = StreakTracking.objects.filter(user=user).aggregate(
                max_streak=Count('longest_streak')
            )['max_streak'] or 0
            if max_streak >= threshold:
                earned = True
        
        if earned:
            # Award achievement
            AchievementBadge.objects.create(
                user_statistics=user_stats,
                badge_type=achievement_id,
                title=title,
                description=description,
                icon="trophy",
                color="gold",
                unlocked_at=timezone.now()
            )
            
            # Award bonus XP
            bonus_xp = threshold // 10 + 10
            user_stats.add_xp(bonus_xp, f"Achievement: {title}")
            
            # Create insight
            ProductivityInsights.objects.create(
                user=user,
                insight_text=f"🏆 Achievement Unlocked: {title}! {description}",
                insight_type="achievement",
                is_read=False
            )

# Auto-run achievement checks when user stats update
@receiver(post_save, sender=UserStatistics)
def auto_check_achievements(sender, instance, **kwargs):
    """Automatically check for new achievements when user stats update."""
    check_and_award_achievements(instance.user)
