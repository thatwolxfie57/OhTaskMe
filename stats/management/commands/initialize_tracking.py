"""
Management command to initialize real-time statistics tracking for existing users.

This command:
1. Creates UserStatistics for users without them
2. Sets up default StreakTracking entries
3. Calculates historical data where possible
4. Initializes achievement tracking
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from stats.models import (
    UserStatistics, DailyStats, StreakTracking, 
    AchievementBadge, ProductivityInsights
)
from tasks.models import Task

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize real-time statistics tracking for existing users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--recalculate',
            action='store_true',
            help='Recalculate existing statistics',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back for historical data (default: 30)',
        )
    
    def handle(self, *args, **options):
        """Initialize tracking system for all users."""
        
        self.stdout.write(
            self.style.SUCCESS('Initializing real-time statistics tracking...')
        )
        
        users = User.objects.all()
        
        for user in users:
            self.stdout.write(f'Processing user: {user.username}')
            
            # 1. Create or update UserStatistics
            self._initialize_user_statistics(user, options['recalculate'])
            
            # 2. Create default streak tracking
            self._initialize_streak_tracking(user)
            
            # 3. Calculate historical daily stats
            self._calculate_historical_daily_stats(user, options['days'])
            
            # 4. Check for achievements
            self._check_initial_achievements(user)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Completed initialization for {user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Successfully initialized tracking for {users.count()} users!'
            )
        )
    
    def _initialize_user_statistics(self, user, recalculate=False):
        """Create or update UserStatistics for the user."""
        
        user_stats, created = UserStatistics.objects.get_or_create(
            user=user,
            defaults={
                'total_tasks_completed': 0,
                'total_tasks_created': 0,
                'total_xp': 0,
                'current_level': 1,
                'xp_to_next_level': 100,
            }
        )
        
        if created or recalculate:
            # Calculate actual statistics from tasks
            completed_tasks = Task.objects.filter(owner=user, completed=True).count()
            total_tasks = Task.objects.filter(owner=user).count()
            
            user_stats.total_tasks_completed = completed_tasks
            user_stats.total_tasks_created = total_tasks
            
            # Calculate initial XP (retroactive)
            if recalculate or user_stats.total_xp == 0:
                initial_xp = completed_tasks * 10  # Base XP per completed task
                user_stats.total_xp = initial_xp
                user_stats._check_level_up()
            
            user_stats.update_completion_rate()
            user_stats.calculate_productivity_score()
            
            self.stdout.write(f'  - Stats: {completed_tasks}/{total_tasks} tasks, {user_stats.total_xp} XP, Level {user_stats.current_level}')
    
    def _initialize_streak_tracking(self, user):
        """Create default streak tracking entries for the user."""
        
        default_streaks = [
            {
                'streak_type': 'daily_tasks',
                'streak_name': 'Daily Task Completion',
                'description': 'Complete at least 3 tasks daily',
                'target_count': 21,  # 21-day habit
                'milestone_rewards': {
                    'milestones': [
                        {'count': 3, 'xp_reward': 50, 'name': '3-Day Streak'},
                        {'count': 7, 'xp_reward': 100, 'name': 'Week Strong'},
                        {'count': 21, 'xp_reward': 250, 'name': 'Habit Formed', 'create_achievement': True}
                    ]
                }
            },
            {
                'streak_type': 'weekly_goals',
                'streak_name': 'Weekly Planning',
                'description': 'Create events or set goals weekly',
                'target_count': 12,  # 3 months
                'milestone_rewards': {
                    'milestones': [
                        {'count': 4, 'xp_reward': 75, 'name': 'Monthly Planner'},
                        {'count': 12, 'xp_reward': 200, 'name': 'Planning Master'}
                    ]
                }
            },
            {
                'streak_type': 'early_completions',
                'streak_name': 'Early Bird',
                'description': 'Complete tasks before scheduled time',
                'target_count': 10,
                'milestone_rewards': {
                    'milestones': [
                        {'count': 5, 'xp_reward': 60, 'name': 'Punctual Pro'},
                        {'count': 10, 'xp_reward': 150, 'name': 'Time Master'}
                    ]
                }
            }
        ]
        
        for streak_config in default_streaks:
            # Add today's date as last_updated
            streak_config['last_updated'] = timezone.now().date()
            
            streak, created = StreakTracking.objects.get_or_create(
                user=user,
                streak_type=streak_config['streak_type'],
                streak_name=streak_config['streak_name'],
                defaults=streak_config
            )
            
            if created:
                self.stdout.write(f'  - Created streak: {streak.streak_name}')
    
    def _calculate_historical_daily_stats(self, user, days_back):
        """Calculate historical daily statistics from existing task data."""
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        current_date = start_date
        created_count = 0
        
        while current_date <= end_date:
            # Check if DailyStats already exists for this date
            if not DailyStats.objects.filter(user=user, date=current_date).exists():
                
                # Calculate tasks completed on this date
                tasks_completed = Task.objects.filter(
                    owner=user,
                    completed=True,
                    completed_at__date=current_date
                ).count()
                
                # Calculate tasks that became overdue on this date
                tasks_overdue = Task.objects.filter(
                    owner=user,
                    completed=False,
                    scheduled_time__date=current_date,
                    scheduled_time__lt=timezone.now()
                ).count()
                
                # Calculate productivity score
                productivity_score = min(tasks_completed * 12 + max(0, 5 - tasks_overdue * 2), 100)
                
                # Create daily stats entry
                if tasks_completed > 0 or tasks_overdue > 0:  # Only create if there's activity
                    DailyStats.objects.create(
                        user=user,
                        date=current_date,
                        tasks_completed=tasks_completed,
                        tasks_overdue=tasks_overdue,
                        daily_productivity_score=productivity_score
                    )
                    created_count += 1
            
            current_date += timedelta(days=1)
        
        if created_count > 0:
            self.stdout.write(f'  - Created {created_count} historical daily stats entries')
    
    def _check_initial_achievements(self, user):
        """Check and award initial achievements for the user."""
        
        user_stats = UserStatistics.objects.get(user=user)
        
        # Basic achievement checks
        achievements_to_check = []
        
        if user_stats.total_tasks_completed >= 1:
            achievements_to_check.append(('first_task', 'First Step', 'Completed your first task!'))
        
        if user_stats.total_tasks_completed >= 10:
            achievements_to_check.append(('task_novice', 'Task Novice', 'Completed 10 tasks!'))
        
        if user_stats.total_tasks_completed >= 50:
            achievements_to_check.append(('task_adept', 'Task Adept', '50 tasks completed!'))
        
        if user_stats.total_xp >= 100:
            achievements_to_check.append(('xp_beginner', 'Getting Started', 'Earned 100 XP!'))
        
        for achievement_type, title, description in achievements_to_check:
            badge, created = AchievementBadge.objects.get_or_create(
                user_statistics=user_stats,
                badge_type=achievement_type,
                defaults={
                    'title': title,
                    'description': description,
                    'icon': 'fas fa-trophy',
                    'color': 'gold',
                    'unlocked_at': timezone.now()
                }
            )
            
            if created:
                self.stdout.write(f'  - Awarded achievement: {title}')
        
        # Create welcome insight
        welcome_insight, created = ProductivityInsights.objects.get_or_create(
            user=user,
            insight_type='productivity_tip',
            title='Welcome to Your Productivity Journey!',
            defaults={
                'message': (
                    'Welcome to your productivity journey! 🚀 '
                    'Your real-time statistics tracking is now active. '
                    'Complete tasks, build streaks, and unlock achievements to level up!'
                ),
                'confidence_score': 1.0,
                'priority': 'medium',
                'is_read': False
            }
        )
