from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.contrib.auth.models import User
from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .models import UserProfile
from .serializers import GoogleAuthSerializer, UserDetailSerializer

import logging

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """
    Generate JWT access and refresh tokens for a user.
    Called after successful Google OAuth verification.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class GoogleAuthView(APIView):
    """
    POST /api/auth/google/
    
    Receives Google OAuth token from frontend.
    Verifies it with Google, creates/finds user in DB,
    and returns JWT tokens.
    
    Request body:
    {
        "token": "google_oauth_token_here"
    }
    
    Response:
    {
        "access": "jwt_access_token",
        "refresh": "jwt_refresh_token",
        "user": { user details }
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        google_token = serializer.validated_data['token']

        try:
            # Verify the Google token
            google_user_info = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            # Extract user info from Google
            google_id = google_user_info.get('sub')
            email = google_user_info.get('email')
            first_name = google_user_info.get('given_name', '')
            last_name = google_user_info.get('family_name', '')
            profile_picture = google_user_info.get('picture', '')

            # Validate required fields
            if not email or not google_id:
                return Response(
                    {'error': 'Invalid Google token: missing email or ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create the user in database
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )

            # Update name if user already exists
            if not user_created:
                user.first_name = first_name
                user.last_name = last_name
                user.save()

            # Get or create user profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'google_id': google_id,
                    'profile_picture': profile_picture,
                }
            )

            # Update profile picture if changed
            if not profile_created:
                profile.profile_picture = profile_picture
                profile.save()

            # Generate JWT tokens
            tokens = get_tokens_for_user(user)

            # Serialize user data
            user_data = UserDetailSerializer(user).data

            logger.info(f"User logged in: {email} (new: {user_created})")

            return Response({
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': user_data,
                'is_new_user': user_created,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.error(f"Google token verification failed: {str(e)}")
            return Response(
                {'error': 'Invalid Google token. Please try again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Google auth error: {str(e)}")
            return Response(
                {'error': 'Authentication failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserDetailView(APIView):
    """
    GET /api/auth/user/

    Returns current authenticated user's details.
    Requires JWT token in Authorization header.

    Headers:
    Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklists the refresh token to logout user.

    Request body:
    {
        "refresh": "jwt_refresh_token"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User logged out: {request.user.email}")
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Logout failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )