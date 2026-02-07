from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import UserCreateSerializer, UserDetailSerializer, UserUpdateSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    API view to register a new user.
    
    This endpoint is publicly accessible (no authentication required).
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Register New User",
        operation_description="""
        Register a new user account in the system.
        
        This endpoint creates a new user with the provided credentials.
        No authentication is required for this endpoint.
        
        Features:
        - Email validation and uniqueness checking
        - Password strength validation
        - Automatic timezone detection and setup
        - User profile initialization
        """,
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=UserDetailSerializer
            ),
            400: openapi.Response(
                description="Validation errors",
                examples={
                    "application/json": {
                        "email": ["User with this email already exists."],
                        "password": ["This password is too common."]
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve or update the authenticated user's profile.
    
    Uses different serializers for GET and PATCH operations.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get User Profile",
        operation_description="""
        Retrieve the authenticated user's profile information.
        
        Returns complete user profile data including:
        - Basic user information (username, email, first/last name)
        - User preferences and settings
        - Timezone information
        - Account creation and last login dates
        """,
        responses={
            200: openapi.Response(
                description="User profile data",
                schema=UserDetailSerializer
            ),
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update User Profile",
        operation_description="""
        Update the authenticated user's profile information.
        
        Allows partial updates of user profile fields including:
        - Name fields (first_name, last_name)
        - Timezone preferences
        - Other profile settings
        
        Password changes should be done through dedicated password change endpoints.
        """,
        request_body=UserUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=UserDetailSerializer
            ),
            400: openapi.Response(description="Validation errors"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def get_object(self):
        """
        Return the authenticated user.
        """
        return self.request.user
    
    def get_serializer_class(self):
        """
        Return different serializers based on the HTTP method.
        """
        if self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserDetailSerializer
