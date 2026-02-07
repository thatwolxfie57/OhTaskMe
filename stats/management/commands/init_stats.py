from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from stats.models import (
    UserStatistics, DailyStats, AchievementBadge, 
    StreakTracking, UserGoals, ProductivityInsights
)
from tasks.models import Task
from events.models import Event
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize statistics system with sample data and achievements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to initialize statistics for (default: all users)',
        )
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample goals and streaks for demonstration',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        create_sample = options.get('create_sample_data', False)
        
        if username:
            try:
                users = [User.objects.get(username=username)]
                self.stdout.write(f"Initializing statistics for user: {username}")
            except User.DoesNotExist:
                self.stderr.write(f"User '{username}' not found")
                return
        else:
            users = User.objects.all()
            self.stdout.write(f"Initializing statistics for all {users.count()} users")

        for user in users:
            self.initialize_user_statistics(user, create_sample)

        self.stdout.write(
            self.style.SUCCESS('Successfully initialized statistics system!')
        )

    def initialize_user_statistics(self, user, create_sample_data=False):
        """Initialize statistics for a specific user."""
        self.stdout.write(f"Processing user: {user.username}")
        
        # Create or get user statistics
        user_stats, created = UserStatistics.objects.get_or_create(user=user)
        
        if created:
            self.stdout.write(f"  ✓ Created UserStatistics for {user.username}")
        else:
            self.stdout.write(f"  → UserStatistics already exists for {user.username}")

        # Update statistics based on existing tasks and events
        self.update_task_statistics(user, user_stats)
        self.create_initial_achievements(user, user_stats)
        self.create_initial_streaks(user)
        
        if create_sample_data:
            self.create_sample_goals(user)
            self.create_sample_insights(user)

        # Recalculate productivity score
        user_stats.calculate_productivity_score()
        
        self.stdout.write(f"  ✓ Completed initialization for {user.username}")

    def update_task_statistics(self, user, user_stats):
        """Update task statistics based on existing data."""
        tasks = Task.objects.filter(owner=user)
        completed_tasks = tasks.filter(completed=True)
        overdue_tasks = tasks.filter(
            scheduled_time__lt=timezone.now(),
            completed=False
        )
        
        user_stats.total_tasks_created = tasks.count()
        user_stats.total_tasks_completed = completed_tasks.count()
        user_stats.total_tasks_overdue = overdue_tasks.count()
        
        # Update completion rate
        user_stats.update_completion_rate()
        
        # Award XP for existing completed tasks (if not already awarded)
        if user_stats.total_xp == 0 and completed_tasks.exists():
            xp_to_award = min(completed_tasks.count() * 10, 200)  # Cap at 200 XP
            user_stats.add_xp(xp_to_award, "Retroactive task completion bonus")
        
        user_stats.save()
        
        self.stdout.write(f"    → Updated task statistics: {user_stats.total_tasks_completed}/{user_stats.total_tasks_created} completed")

    def create_initial_achievements(self, user, user_stats):
        """Create initial achievements for the user."""
        achievements_to_create = []
        
        # First task achievement
        if user_stats.total_tasks_completed > 0:
            achievements_to_create.append({
                'badge_type': 'first_task',
                'title': 'First Steps',
                'description': 'Completed your first task!',
                'icon': 'fas fa-baby',
                'color': 'success'
            })
        
        # Early adopter achievement
        achievements_to_create.append({
            'badge_type': 'custom',
            'title': 'Early Adopter',
            'description': 'Joined the OhTaskMe statistics system!',
            'icon': 'fas fa-rocket',
            'color': 'primary'
        })
        
        # Productivity milestones
        if user_stats.total_tasks_completed >= 10:
            achievements_to_create.append({
                'badge_type': 'productivity_guru',
                'title': 'Getting Things Done',
                'description': 'Completed 10 tasks!',
                'icon': 'fas fa-check-double',
                'color': 'warning'
            })
        
        if user_stats.total_tasks_completed >= 25:
            achievements_to_create.append({
                'badge_type': 'productivity_guru',
                'title': 'Task Master',
                'description': 'Completed 25 tasks!',
                'icon': 'fas fa-crown',
                'color': 'gold',
                'is_rare': True
            })
        
        # Create achievements
        for achievement_data in achievements_to_create:
            achievement, created = AchievementBadge.objects.get_or_create(
                user_statistics=user_stats,
                badge_type=achievement_data['badge_type'],
                title=achievement_data['title'],
                defaults={
                    'description': achievement_data['description'],
                    'icon': achievement_data['icon'],
                    'color': achievement_data['color'],
                    'is_rare': achievement_data.get('is_rare', False),
                    'unlocked_at': timezone.now()
                }
            )
            
            if created:
                self.stdout.write(f"    ✓ Created achievement: {achievement.title}")

    def create_initial_streaks(self, user):
        """Create initial streak tracking for the user."""
        streaks_to_create = [
            {
                'streak_type': 'daily_tasks',
                'streak_name': 'Daily Task Completion',
                'description': 'Complete at least one task every day',
                'target_count': 7,
                'milestone_rewards': {
                    'milestones': [
                        {
                            'count': 3,
                            'name': '3-Day Streak',
                            'xp_reward': 30,
                            'create_achievement': True,
                            'achievement_title': '3-Day Warrior',
                            'achievement_description': 'Maintained a 3-day task completion streak'
                        },
                        {
                            'count': 7,
                            'name': 'Week Champion',
                            'xp_reward': 100,
                            'create_achievement': True,
                            'achievement_title': 'Week Champion',
                            'achievement_description': 'Completed tasks for 7 consecutive days'
                        }
                    ]
                }
            },
            {
                'streak_type': 'perfect_days',
                'streak_name': 'Perfect Days',
                'description': 'Complete all scheduled tasks in a day',
                'target_count': 5,
                'milestone_rewards': {
                    'milestones': [
                        {
                            'count': 1,
                            'name': 'Perfect Day',
                            'xp_reward': 50,
                            'create_achievement': True,
                            'achievement_title': 'Perfect Day',
                            'achievement_description': 'Completed all tasks in a single day'
                        }
                    ]
                }
            }
        ]
        
        for streak_data in streaks_to_create:
            streak, created = StreakTracking.objects.get_or_create(
                user=user,
                streak_type=streak_data['streak_type'],
                streak_name=streak_data['streak_name'],
                defaults={
                    'description': streak_data['description'],
                    'target_count': streak_data['target_count'],
                    'milestone_rewards': streak_data['milestone_rewards'],
                    'last_updated': timezone.now().date()
                }
            )
            
            if created:
                self.stdout.write(f"    ✓ Created streak: {streak.streak_name}")

    def create_sample_goals(self, user):
        """Create sample goals for demonstration."""
        sample_goals = [
            {
                'goal_type': 'weekly',
                'title': 'Complete 10 Tasks This Week',
                'description': 'Stay productive and complete at least 10 tasks this week',
                'target_value': 10,
                'progress_unit': 'tasks',
                'target_date': timezone.now().date() + timedelta(days=7),
                'reward_xp': 150,
                'custom_reward': 'Treat yourself to your favorite coffee'
            },
            {
                'goal_type': 'monthly',
                'title': 'Monthly Productivity Goal',
                'description': 'Achieve a productivity score of 80% this month',
                'target_value': 80,
                'progress_unit': 'percentage',
                'target_date': timezone.now().date() + timedelta(days=30),
                'reward_xp': 300,
                'custom_reward': 'Buy that book you\'ve been wanting'
            }
        ]
        
        for goal_data in sample_goals:
            goal, created = UserGoals.objects.get_or_create(
                user=user,
                title=goal_data['title'],
                defaults={
                    'goal_type': goal_data['goal_type'],
                    'description': goal_data['description'],
                    'target_value': goal_data['target_value'],
                    'progress_unit': goal_data['progress_unit'],
                    'start_date': timezone.now().date(),
                    'target_date': goal_data['target_date'],
                    'reward_xp': goal_data['reward_xp'],
                    'custom_reward': goal_data['custom_reward']
                }
            )
            
            if created:
                self.stdout.write(f"    ✓ Created sample goal: {goal.title}")

    def create_sample_insights(self, user):
        """Create sample productivity insights."""
        sample_insights = [
            {
                'insight_type': 'productivity_tip',
                'title': 'Welcome to Your Statistics Dashboard!',
                'message': 'Track your progress, set goals, and earn achievements as you complete tasks. Your productivity journey starts here!',
                'confidence_score': 1.0,
                'priority': 'high'
            },
            {
                'insight_type': 'habit_suggestion',
                'title': 'Build a Daily Task Habit',
                'message': 'Consider completing at least one task every day to build momentum and maintain your productivity streak.',
                'confidence_score': 0.9,
                'priority': 'medium'
            }
        ]
        
        for insight_data in sample_insights:
            insight, created = ProductivityInsights.objects.get_or_create(
                user=user,
                title=insight_data['title'],
                defaults={
                    'insight_type': insight_data['insight_type'],
                    'message': insight_data['message'],
                    'confidence_score': insight_data['confidence_score'],
                    'priority': insight_data['priority']
                }
            )
            
            if created:
                self.stdout.write(f"    ✓ Created insight: {insight.title}")
