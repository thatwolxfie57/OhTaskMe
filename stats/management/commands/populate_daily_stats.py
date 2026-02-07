from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from stats.models import DailyStats, UserStatistics
from random import randint

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate daily statistics with sample data for testing charts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to create stats for (default: all users)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of sample data to create (default: 30)',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        days = options.get('days', 30)
        
        if username:
            try:
                users = [User.objects.get(username=username)]
                self.stdout.write(f"Creating stats for user: {username}")
            except User.DoesNotExist:
                self.stderr.write(f"User '{username}' not found")
                return
        else:
            users = User.objects.all()
            self.stdout.write(f"Creating stats for all {users.count()} users")

        end_date = timezone.now().date()
        
        for user in users:
            # Ensure user has statistics
            user_stats, created = UserStatistics.objects.get_or_create(user=user)
            
            # Check if user already has daily stats
            existing_stats = DailyStats.objects.filter(user=user).count()
            
            if existing_stats > 0:
                self.stdout.write(f"  {user.username}: Already has {existing_stats} daily stats records")
                continue
            
            self.stdout.write(f"  Creating {days} days of sample data for {user.username}...")
            
            total_xp_awarded = 0
            
            for i in range(days):
                date = end_date - timedelta(days=days-1-i)
                
                # Create realistic sample data
                tasks_created = randint(1, 10)
                tasks_completed = randint(0, tasks_created)
                completion_rate = (tasks_completed / tasks_created) * 100 if tasks_created > 0 else 0
                
                # Base productivity score on completion rate with some variance
                base_score = completion_rate
                productivity_score = max(min(base_score + randint(-20, 20), 100), 0)
                
                # Weekend penalty (lower activity)
                if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    productivity_score *= 0.7
                    tasks_completed = max(tasks_completed - randint(1, 3), 0)
                
                daily_stats = DailyStats.objects.create(
                    user=user,
                    date=date,
                    tasks_created=tasks_created,
                    tasks_completed=tasks_completed,
                    tasks_overdue=randint(0, max(tasks_created - tasks_completed, 0)),
                    events_attended=randint(0, 3),
                    total_work_time=randint(120, 480),  # 2-8 hours in minutes
                    focus_time=randint(60, 240),  # 1-4 hours of focused work
                    daily_productivity_score=productivity_score,
                    mood_rating=randint(4, 9),
                    energy_level=randint(3, 8),
                    daily_goal_set=randint(0, 1) == 1,
                    daily_goal_achieved=randint(0, 1) == 1 if randint(0, 1) == 1 else False
                )
                
                # Award XP for completed tasks
                if tasks_completed > 0:
                    xp_earned = tasks_completed * randint(8, 15)
                    total_xp_awarded += xp_earned
            
            # Update user statistics
            if total_xp_awarded > 0:
                user_stats.add_xp(total_xp_awarded, f"Sample data initialization - {days} days")
            
            self.stdout.write(
                self.style.SUCCESS(f"    ✓ Created {days} daily stats records for {user.username} (+{total_xp_awarded} XP)")
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated daily statistics!')
        )
