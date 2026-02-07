from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        """
        Validate that passwords match and meet Django's password requirements.
        """
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        return attrs

class PasswordResetRequestView(APIView):
    """
    API view to request a password reset.
    
    This endpoint is publicly accessible (no authentication required).
    It sends an email with a password reset link containing a token.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @swagger_auto_schema(
        operation_summary="Request Password Reset",
        operation_description="""
        Send a password reset email to the user.
        
        This endpoint accepts an email address and sends a password reset
        email if a user with that email exists. For security reasons,
        the endpoint always returns success even if the email doesn't exist.
        
        The email contains a secure token that expires after a set time period.
        """,
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Password reset email sent (or would be sent)",
                examples={
                    "application/json": {
                        "message": "If an account with that email exists, a password reset email has been sent."
                    }
                }
            ),
            400: openapi.Response(description="Invalid email format")
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                # Generate token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build reset URL (frontend would handle this route)
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
                
                # Send email
                send_mail(
                    subject="Password Reset Request",
                    message=f"Please reset your password by clicking the link below:\n\n{reset_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                return Response(
                    {"detail": "Password reset email has been sent."},
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                # We don't want to reveal which emails are in the database
                return Response(
                    {"detail": "Password reset email has been sent."},
                    status=status.HTTP_200_OK
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    """
    API view to confirm a password reset.
    
    This endpoint is publicly accessible (no authentication required).
    It verifies the token and changes the user's password.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @swagger_auto_schema(
        operation_summary="Confirm Password Reset",
        operation_description="""
        Complete the password reset process using the token from email.
        
        This endpoint accepts the UID and token from the password reset email,
        along with the new password. It verifies the token and updates the
        user's password if everything is valid.
        
        The token has an expiration time and can only be used once.
        """,
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successful",
                examples={
                    "application/json": {
                        "message": "Password has been reset successfully."
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid token, passwords don't match, or other validation error",
                examples={
                    "application/json": {
                        "error": "Invalid token or user ID."
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
                user = User.objects.get(pk=uid)
                
                # Verify token
                if default_token_generator.check_token(user, serializer.validated_data['token']):
                    # Set new password
                    user.set_password(serializer.validated_data['new_password'])
                    user.save()
                    
                    return Response(
                        {"detail": "Password has been reset successfully."},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"detail": "Invalid token."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {"detail": "Invalid user ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
