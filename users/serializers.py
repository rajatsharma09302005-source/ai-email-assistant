from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""

    class Meta:
        model = UserProfile
        fields = [
            'google_id',
            'profile_picture',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django's built-in User model."""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'profile'
        ]
        read_only_fields = ['id', 'username']


class GoogleAuthSerializer(serializers.Serializer):
    """
    Serializer to validate Google OAuth token sent from frontend.
    Frontend sends the token after user clicks 'Login with Google'.
    """
    token = serializers.CharField(required=True)

    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError("Google token is required.")
        return value


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with profile info.
    Used for GET /api/auth/user/ endpoint.
    """
    profile_picture = serializers.SerializerMethodField()
    google_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'username',
            'profile_picture',
            'google_id',
        ]

    def get_profile_picture(self, obj):
        try:
            return obj.profile.profile_picture
        except UserProfile.DoesNotExist:
            return None

    def get_google_id(self, obj):
        try:
            return obj.profile.google_id
        except UserProfile.DoesNotExist:
            return None