from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core import management
from datetime import datetime, timedelta, date
import json

from stats.models import (
    UserStatistics, DailyStats, AchievementBadge, 
    StreakTracking, UserGoals, XPLog, ProductivityInsights
)
from tasks.models import Task
from events.models import Event

User = get_user_model()


class UserStatisticsModelTest(TestCase):
    """Test UserStatistics model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_stats = UserStatistics.objects.create(user=self.user)
    
    def test_user_statistics_creation(self):
        """Test UserStatistics model creation with default values."""
        self.assertEqual(self.user_stats.user, self.user)
        self.assertEqual(self.user_stats.total_xp, 0)
        self.assertEqual(self.user_stats.current_level, 1)
        self.assertEqual(self.user_stats.xp_to_next_level, 100)
        self.assertEqual(self.user_stats.productivity_score, 0.0)
        self.assertEqual(self.user_stats.completion_rate, 0.0)
    
    def test_add_xp_functionality(self):
        """Test XP addition and level progression."""
        initial_xp = self.user_stats.total_xp
        self.user_stats.add_xp(50, "Test XP")
        
        self.assertEqual(self.user_stats.total_xp, initial_xp + 50)
        
        # Check XP log creation
        xp_log = XPLog.objects.filter(user_statistics=self.user_stats).first()
        self.assertIsNotNone(xp_log)
        self.assertEqual(xp_log.points_earned, 50)
        self.assertEqual(xp_log.reason, "Test XP")
    
    def test_level_progression(self):
        """Test automatic level progression when XP threshold is reached."""
        # Add enough XP to level up (100 XP for level 1 -> 2)
        self.user_stats.add_xp(100, "Level up test")
        
        self.assertEqual(self.user_stats.current_level, 2)
        # Level 2 requirement is 150 (100 * 1.5^1)
        self.assertEqual(self.user_stats.xp_to_next_level, 150)
        
        # Check achievement creation for level up
        level_achievement = AchievementBadge.objects.filter(
            user_statistics=self.user_stats,
            badge_type='level'
        ).first()
        self.assertIsNotNone(level_achievement)
    
    def test_completion_rate_calculation(self):
        """Test task completion rate calculation."""
        self.user_stats.total_tasks_created = 10
        self.user_stats.total_tasks_completed = 7
        self.user_stats.update_completion_rate()
        
        self.assertEqual(self.user_stats.completion_rate, 70.0)
    
    def test_productivity_score_calculation(self):
        """Test productivity score calculation based on multiple factors."""
        self.user_stats.completion_rate = 80.0
        self.user_stats.punctuality_score = 90.0
        self.user_stats.current_daily_streak = 5
        self.user_stats.current_weekly_streak = 2
        
        score = self.user_stats.calculate_productivity_score()
        
        # Expected: 80*0.4 + 90*0.3 + 5*2 + 2*1 = 32 + 27 + 10 + 2 = 71
        self.assertEqual(score, 71.0)
        self.assertEqual(self.user_stats.productivity_score, 71.0)
    
    def test_xp_remaining_to_next_level_property(self):
        """Test the XP remaining calculation property."""
        self.user_stats.total_xp = 75
        self.user_stats.xp_to_next_level = 100
        
        remaining = self.user_stats.xp_remaining_to_next_level
        self.assertEqual(remaining, 25)


class DailyStatsModelTest(TestCase):
    """Test DailyStats model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='dailyuser',
            email='daily@example.com',
            password='testpass123'
        )
    
    def test_daily_stats_creation(self):
        """Test DailyStats creation with default values."""
        today = timezone.now().date()
        daily_stats = DailyStats.objects.create(
            user=self.user,
            date=today
        )
        
        self.assertEqual(daily_stats.user, self.user)
        self.assertEqual(daily_stats.date, today)
        self.assertEqual(daily_stats.tasks_completed, 0)
        self.assertEqual(daily_stats.mood_rating, 5)
        self.assertEqual(daily_stats.energy_level, 5)
    
    def test_get_or_create_today_method(self):
        """Test the get_or_create_today class method."""
        daily_stats = DailyStats.get_or_create_today(self.user)
        
        self.assertIsNotNone(daily_stats)
        self.assertEqual(daily_stats.date, timezone.now().date())
        self.assertEqual(daily_stats.user, self.user)
        
        # Test that calling again returns the same instance
        daily_stats2 = DailyStats.get_or_create_today(self.user)
        self.assertEqual(daily_stats.pk, daily_stats2.pk)


class AchievementBadgeModelTest(TestCase):
    """Test AchievementBadge model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='achiever',
            email='achiever@example.com',
            password='testpass123'
        )
        self.user_stats = UserStatistics.objects.create(user=self.user)
    
    def test_achievement_creation(self):
        """Test achievement badge creation."""
        achievement = AchievementBadge.objects.create(
            user_statistics=self.user_stats,
            badge_type='first_task',
            title='First Task Completed',
            description='Completed your first task!',
            unlocked_at=timezone.now()
        )
        
        self.assertEqual(achievement.user_statistics, self.user_stats)
        self.assertEqual(achievement.badge_type, 'first_task')
        self.assertEqual(achievement.title, 'First Task Completed')
        self.assertEqual(achievement.rarity_level, 'common')
        self.assertFalse(achievement.is_rare)
    
    def test_rare_achievement_creation(self):
        """Test rare achievement creation."""
        achievement = AchievementBadge.objects.create(
            user_statistics=self.user_stats,
            badge_type='productivity_guru',
            title='Productivity Master',
            description='Achieved exceptional productivity!',
            is_rare=True,
            rarity_level='epic',
            unlocked_at=timezone.now()
        )
        
        self.assertTrue(achievement.is_rare)
        self.assertEqual(achievement.rarity_level, 'epic')


class StreakTrackingModelTest(TestCase):
    """Test StreakTracking model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='streaker',
            email='streaker@example.com',
            password='testpass123'
        )
    
    def test_streak_creation(self):
        """Test streak tracking creation."""
        streak = StreakTracking.objects.create(
            user=self.user,
            streak_type='daily_tasks',
            streak_name='Daily Task Completion',
            description='Complete at least one task daily',
            last_updated=timezone.now().date()
        )
        
        self.assertEqual(streak.user, self.user)
        self.assertEqual(streak.current_count, 0)
        self.assertEqual(streak.best_count, 0)
        self.assertTrue(streak.is_active)
    
    def test_increment_streak(self):
        """Test streak increment functionality."""
        streak = StreakTracking.objects.create(
            user=self.user,
            streak_type='daily_tasks',
            streak_name='Test Streak',
            last_updated=timezone.now().date()
        )
        
        initial_count = streak.current_count
        streak.increment_streak()
        
        self.assertEqual(streak.current_count, initial_count + 1)
        self.assertEqual(streak.best_count, 1)
        self.assertEqual(streak.last_updated, timezone.now().date())
    
    def test_break_streak(self):
        """Test streak breaking functionality."""
        streak = StreakTracking.objects.create(
            user=self.user,
            streak_type='daily_tasks',
            streak_name='Test Streak',
            current_count=5,
            best_count=5,
            last_updated=timezone.now().date()
        )
        
        streak.break_streak()
        
        self.assertEqual(streak.current_count, 0)
        self.assertEqual(streak.best_count, 5)  # Best count should remain


class UserGoalsModelTest(TestCase):
    """Test UserGoals model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='goaluser',
            email='goals@example.com',
            password='testpass123'
        )
        self.user_stats = UserStatistics.objects.create(user=self.user)
    
    def test_goal_creation(self):
        """Test goal creation with default values."""
        target_date = timezone.now().date() + timedelta(days=7)
        goal = UserGoals.objects.create(
            user=self.user,
            goal_type='weekly',
            title='Complete 10 Tasks',
            target_value=10,
            start_date=timezone.now().date(),
            target_date=target_date
        )
        
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.current_progress, 0)
        self.assertEqual(goal.status, 'active')
        self.assertEqual(goal.progress_unit, 'tasks')
    
    def test_progress_percentage_property(self):
        """Test progress percentage calculation."""
        goal = UserGoals.objects.create(
            user=self.user,
            goal_type='weekly',
            title='Test Goal',
            target_value=100,
            current_progress=25,
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=7)
        )
        
        self.assertEqual(goal.progress_percentage, 25.0)
    
    def test_days_remaining_property(self):
        """Test days remaining calculation."""
        target_date = timezone.now().date() + timedelta(days=5)
        goal = UserGoals.objects.create(
            user=self.user,
            goal_type='weekly',
            title='Test Goal',
            target_value=10,
            start_date=timezone.now().date(),
            target_date=target_date
        )
        
        self.assertEqual(goal.days_remaining, 5)
    
    def test_update_progress(self):
        """Test goal progress update."""
        goal = UserGoals.objects.create(
            user=self.user,
            goal_type='weekly',
            title='Test Goal',
            target_value=10,
            current_progress=5,
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=7)
        )
        
        goal.update_progress(3)
        self.assertEqual(goal.current_progress, 8)
        
        # Test completion
        goal.update_progress(2)
        self.assertEqual(goal.status, 'completed')
        self.assertIsNotNone(goal.completed_date)


class StatisticsViewsTest(TestCase):
    """Test statistics views functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewuser',
            email='view@example.com',
            password='testpass123'
        )
        self.user_stats = UserStatistics.objects.create(user=self.user)
        self.client.login(username='viewuser', password='testpass123')
    
    def test_statistics_dashboard_view(self):
        """Test statistics dashboard view accessibility and context."""
        url = reverse('stats:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Statistics Dashboard')
        self.assertIn('user_stats', response.context)
        self.assertIn('chart_data', response.context)
    
    def test_achievements_gallery_view(self):
        """Test achievements gallery view."""
        # Create a test achievement
        AchievementBadge.objects.create(
            user_statistics=self.user_stats,
            badge_type='first_task',
            title='Test Achievement',
            description='Test description',
            unlocked_at=timezone.now()
        )
        
        url = reverse('stats:achievements')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Achievements Gallery')
        self.assertContains(response, 'Test Achievement')
    
    def test_goals_management_view_get(self):
        """Test goals management view GET request."""
        url = reverse('stats:goals_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Goals Management')
    
    def test_goals_management_view_post(self):
        """Test goals management view POST request (create goal)."""
        url = reverse('stats:goals_management')
        target_date = (timezone.now().date() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        response = self.client.post(url, {
            'goal_type': 'weekly',
            'title': 'Test Goal Creation',
            'description': 'Test goal description',
            'target_value': 15,
            'progress_unit': 'tasks',
            'target_date': target_date,
            'reward_xp': 200,
            'custom_reward': 'Test reward'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # Check goal was created
        goal = UserGoals.objects.filter(user=self.user, title='Test Goal Creation').first()
        self.assertIsNotNone(goal)
        if goal:
            self.assertEqual(goal.target_value, 15)
    
    def test_update_goal_progress_view(self):
        """Test goal progress update AJAX view."""
        goal = UserGoals.objects.create(
            user=self.user,
            goal_type='weekly',
            title='Progress Test Goal',
            target_value=10,
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=7)
        )
        
        url = reverse('stats:update_goal_progress', kwargs={'goal_id': goal.pk})
        response = self.client.post(url, {'increment': 3})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['current_progress'], 3)
        self.assertEqual(data['progress_percentage'], 30.0)
    
    def test_unauthorized_access(self):
        """Test that views require authentication."""
        self.client.logout()
        
        urls = [
            reverse('stats:dashboard'),
            reverse('stats:achievements'),
            reverse('stats:goals_management'),
            reverse('stats:streaks'),
            reverse('stats:insights'),
            reverse('stats:mood_tracking'),
            reverse('stats:api_data'),
            reverse('stats:api_dashboard'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            # Should redirect to login (302) or return unauthorized (401/403)
            self.assertIn(response.status_code, [302, 401, 403])


class StatisticsIntegrationTest(TestCase):
    """Test integration between statistics and other app components."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integration',
            email='integration@example.com',
            password='testpass123'
        )
        self.user_stats = UserStatistics.objects.create(user=self.user)
    
    def test_task_completion_integration(self):
        """Test that task completion updates statistics."""
        # Create some tasks
        task1 = Task.objects.create(
            owner=self.user,
            description='Test Task 1',
            scheduled_time=timezone.now()
        )
        Task.objects.create(
            owner=self.user,
            description='Test Task 2',
            scheduled_time=timezone.now()
        )
        
        # Update statistics based on tasks (simulating what init_stats does)
        tasks = Task.objects.filter(owner=self.user)
        completed_tasks = tasks.filter(completed=True)
        
        self.user_stats.total_tasks_created = tasks.count()
        self.user_stats.total_tasks_completed = completed_tasks.count()
        self.user_stats.update_completion_rate()
        
        self.assertEqual(self.user_stats.total_tasks_created, 2)
        self.assertEqual(self.user_stats.total_tasks_completed, 0)
        self.assertEqual(self.user_stats.completion_rate, 0.0)
        
        # Complete a task
        task1.completed = True
        task1.save()
        
        # Update stats again
        completed_tasks = tasks.filter(completed=True)
        self.user_stats.total_tasks_completed = completed_tasks.count()
        self.user_stats.update_completion_rate()
        
        self.assertEqual(self.user_stats.total_tasks_completed, 1)
        self.assertEqual(self.user_stats.completion_rate, 50.0)


class StatisticsManagementCommandTest(TestCase):
    """Test the statistics initialization management command."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='cmduser',
            email='cmd@example.com',
            password='testpass123'
        )
    
    def test_init_stats_command_basic(self):
        """Test basic statistics initialization."""
        # Ensure no stats exist initially
        self.assertFalse(UserStatistics.objects.filter(user=self.user).exists())
        
        # Run the command
        management.call_command('init_stats', user=self.user.username)
        
        # Check that statistics were created
        user_stats = UserStatistics.objects.filter(user=self.user).first()
        self.assertIsNotNone(user_stats)
        
        # Check that achievements were created
        achievements = AchievementBadge.objects.filter(user_statistics=user_stats)
        self.assertTrue(achievements.exists())
        
        # Check that streaks were created
        streaks = StreakTracking.objects.filter(user=self.user)
        self.assertTrue(streaks.exists())


# Create your tests here.
