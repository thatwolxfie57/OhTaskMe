"""
Tests for the Event model and API.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import datetime

# Import Task for relationships
from tasks.models import Task

# Import the Event model and task suggestion functions
from events.models import Event
from events.task_suggestions import generate_task_suggestions, classify_event_type, extract_keywords

User = get_user_model()

class EventModelTests(TestCase):
    """
    Test suite for the Event model.
    """
    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            username='eventuser',
            email='event@example.com',
            password='password123',
            timezone='UTC'
        )
        
        # Create a test event
        self.event = Event.objects.create(
            title='Team Meeting',
            description='Weekly team sync-up',
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=1, hours=1),
            owner=self.user
        )
    
    def test_event_creation(self):
        """
        Test creating an event.
        """
        self.assertEqual(self.event.title, 'Team Meeting')
        self.assertEqual(self.event.owner, self.user)
        self.assertFalse(self.event.is_past)
    
    def test_event_string_representation(self):
        """
        Test string representation of an event.
        """
        self.assertEqual(str(self.event), 'Team Meeting')
    
    def test_is_past_property(self):
        """
        Test the is_past property.
        """
        # Current event should not be past
        self.assertFalse(self.event.is_past)
        
        # Create a past event
        past_event = Event.objects.create(
            title='Past Meeting',
            description='Already happened',
            start_time=timezone.now() - datetime.timedelta(days=2),
            end_time=timezone.now() - datetime.timedelta(days=2, hours=1),
            owner=self.user
        )
        self.assertTrue(past_event.is_past)
    
    def test_check_workload_for_day(self):
        """
        Test checking workload for a day.
        """
        event_date = self.event.start_time.date()
        
        # Initially no tasks for the day
        workload = self.event.check_workload_for_day(event_date)
        self.assertEqual(workload['count'], 0)
        
        # Add tasks for the day
        Task.objects.create(
            description='Prepare agenda',
            scheduled_time=self.event.start_time - datetime.timedelta(hours=2),
            owner=self.user
        )
        
        Task.objects.create(
            description='Follow up',
            scheduled_time=self.event.end_time + datetime.timedelta(hours=1),
            owner=self.user
        )
        
        # Now should have 2 tasks
        workload = self.event.check_workload_for_day(event_date)
        self.assertEqual(workload['count'], 2)

class EventAPITests(TestCase):
    """
    Test suite for the Event API.
    """
    def setUp(self):
        """
        Set up test data.
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='eventapiuser',
            email='eventapi@example.com',
            password='password123',
            timezone='UTC'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create some test events
        self.event1 = Event.objects.create(
            title='Project Kickoff',
            description='Start of new project',
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=1, hours=2),
            owner=self.user
        )
        
        self.event2 = Event.objects.create(
            title='Sprint Planning',
            description='Plan the next sprint',
            start_time=timezone.now() + datetime.timedelta(days=2),
            end_time=timezone.now() + datetime.timedelta(days=2, hours=1),
            owner=self.user
        )
    
    def test_get_events_list(self):
        """
        Test getting list of events.
        """
        url = reverse('events:event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Should have our 2 events
    
    def test_create_event(self):
        """
        Test creating an event via API.
        """
        url = reverse('events:event-list')
        data = {
            'title': 'New Meeting',
            'description': 'Discussion about project',
            'start_time': (timezone.now() + datetime.timedelta(days=3)).isoformat(),
            'end_time': (timezone.now() + datetime.timedelta(days=3, hours=1)).isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 3)  # Now have 3 events
        self.assertEqual(Event.objects.latest('id').title, 'New Meeting')
    
    def test_update_event(self):
        """
        Test updating an event via API.
        """
        url = reverse('events:event-detail', args=[self.event1.id])
        data = {
            'title': 'Updated Project Kickoff',
            'description': self.event1.description,
            'start_time': self.event1.start_time.isoformat(),
            'end_time': self.event1.end_time.isoformat()
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.title, 'Updated Project Kickoff')
    
    def test_delete_event(self):
        """
        Test deleting an event via API.
        """
        url = reverse('events:event-detail', args=[self.event1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Event.objects.count(), 1)  # Only have 1 event now
    
    def test_upcoming_events(self):
        """
        Test getting upcoming events.
        """
        # Create a past event
        Event.objects.create(
            title='Past Meeting',
            description='Already happened',
            start_time=timezone.now() - datetime.timedelta(days=2),
            end_time=timezone.now() - datetime.timedelta(days=2, hours=1),
            owner=self.user
        )
        
        url = reverse('events:event-upcoming')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should have our 2 future events
