from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import datetime

from tasks.models import Task

User = get_user_model()

class TaskModelTests(TestCase):
    """
    Test suite for the Task model.
    """
    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            timezone='UTC'
        )
        self.task = Task.objects.create(
            description='Test Task',
            scheduled_time=timezone.now() + datetime.timedelta(days=1),
            owner=self.user
        )
    
    def test_task_creation(self):
        """
        Test that a task can be created.
        """
        self.assertEqual(self.task.description, 'Test Task')
        self.assertEqual(self.task.owner, self.user)
        self.assertFalse(self.task.completed)
        self.assertIsNone(self.task.completed_at)
    
    def test_mark_as_completed(self):
        """
        Test that a task can be marked as completed.
        """
        self.task.mark_as_completed()
        self.assertTrue(self.task.completed)
        self.assertIsNotNone(self.task.completed_at)
    
    def test_mark_as_incomplete(self):
        """
        Test that a task can be marked as incomplete.
        """
        self.task.mark_as_completed()
        self.task.mark_as_incomplete()
        self.assertFalse(self.task.completed)
        self.assertIsNone(self.task.completed_at)
    
class TaskAPITests(TestCase):
    """
    Test suite for the Task API.
    """
    def setUp(self):
        """
        Set up test client and users.
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            timezone='UTC'
        )
        self.client.force_authenticate(user=self.user)
        self.task_data = {
            'description': 'Test API Task',
            'scheduled_time': (timezone.now() + datetime.timedelta(days=1)).isoformat()
        }
        self.task = Task.objects.create(
            description='Existing Task',
            scheduled_time=timezone.now() + datetime.timedelta(days=2),
            owner=self.user
        )
    
    def test_create_task(self):
        """
        Test creating a task via the API.
        """
        response = self.client.post(reverse('tasks:task-list'), self.task_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(Task.objects.filter(description='Test API Task').count(), 1)
    
    def test_retrieve_task(self):
        """
        Test retrieving a task via the API.
        """
        response = self.client.get(reverse('tasks:task-detail', args=[self.task.id]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Existing Task')
    
    def test_update_task(self):
        """
        Test updating a task via the API.
        """
        update_data = {'description': 'Updated Task'}
        response = self.client.patch(
            reverse('tasks:task-detail', args=[self.task.id]), 
            update_data, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.description, 'Updated Task')
    
    def test_delete_task(self):
        """
        Test deleting a task via the API.
        """
        response = self.client.delete(reverse('tasks:task-detail', args=[self.task.id]), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)
    
    def test_task_complete_action(self):
        """
        Test marking a task as complete via the API.
        """
        response = self.client.post(reverse('tasks:task-complete', args=[self.task.id]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)
        self.assertIsNotNone(self.task.completed_at)
    
    def test_task_incomplete_action(self):
        """
        Test marking a task as incomplete via the API.
        """
        self.task.mark_as_completed()
        response = self.client.post(reverse('tasks:task-incomplete', args=[self.task.id]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertFalse(self.task.completed)
        self.assertIsNone(self.task.completed_at)
