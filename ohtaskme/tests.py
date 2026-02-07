from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()

class ProjectSetupTests(TestCase):
    """
    Test suite for project setup, URL routing and configuration.
    """
    def setUp(self):
        """
        Set up test client and create a test user.
        """
        self.client = Client()
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            timezone='UTC'
        )
    
    def test_admin_site_access(self):
        """
        Test that admin site is accessible.
        """
        response = self.client.get('/admin/', follow=True)
        # Should redirect to login page without 404
        self.assertEqual(response.status_code, 200)
    
    def test_api_root_access(self):
        """
        Test that API endpoints are accessible.
        """
        # Try accessing one of the API endpoints
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get('/api/tasks/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_authentication_required(self):
        """
        Test that authenticated endpoints require authentication.
        """
        # Try accessing tasks API without authentication
        response = self.api_client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Now with authentication
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_static_files_configuration(self):
        """
        Test that static files are served correctly in development.
        """
        # Note: This test might not be meaningful in test environment
        # Instead, let's check if STATIC_URL is correctly configured
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'STATIC_URL'))
        self.assertEqual(settings.STATIC_URL, '/static/')
