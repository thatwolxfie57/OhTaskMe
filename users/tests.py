from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class AuthenticationTests(TestCase):
    """
    Test suite for authentication endpoints.
    """
    def setUp(self):
        """
        Set up test client and create a test user.
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            timezone='UTC'
        )
        self.register_url = reverse('users:register')
        self.token_url = reverse('users:token_obtain_pair')
        self.token_refresh_url = reverse('users:token_refresh')
        self.profile_url = reverse('users:profile')
        self.password_reset_url = reverse('users:password_reset_request')
        self.password_reset_confirm_url = reverse('users:password_reset_confirm')

    def test_user_registration(self):
        """
        Test user registration endpoint.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
            'timezone': 'UTC'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """
        Test user login and token generation.
        """
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(self.token_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        """
        Test token refresh endpoint.
        """
        # First get a refresh token
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        login_response = self.client.post(self.token_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Now try to refresh the token
        refresh_data = {
            'refresh': refresh_token
        }
        response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_profile_access(self):
        """
        Test that the profile endpoint is accessible with authentication.
        """
        # Try without authentication
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try with authentication
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        login_response = self.client.post(self.token_url, login_data, format='json')
        access_token = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_password_reset_request(self):
        """
        Test password reset request endpoint.
        """
        data = {
            'email': 'test@example.com'
        }
        response = self.client.post(self.password_reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
