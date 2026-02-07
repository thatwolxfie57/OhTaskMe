from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Includes fields for creating a new user and handles password validation and hashing.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'timezone']
        extra_kwargs = {
            'email': {'required': True},
            'timezone': {'required': False}
        }
    
    def validate(self, attrs):
        """
        Validate that the passwords match and meet Django's password requirements.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        return attrs
    
    def create(self, validated_data):
        """
        Create and return a new user with encrypted password and default timezone.
        """
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            timezone=validated_data.get('timezone', 'UTC')
        )
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user details.
    
    Used for user profile display and updates.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'timezone']
        read_only_fields = ['id', 'username', 'email']


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    
    Allows updating first_name, last_name, and timezone.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'timezone']
