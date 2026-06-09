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
            
            
            
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import json

class GmailOAuthInitView(APIView):
    """
    GET /api/auth/gmail/init/
    Initiates Gmail OAuth flow to get Gmail access token.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Gmail OAuth scopes
        SCOPES = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
        ]

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:5173/gmail/callback"],
                }
            },
            scopes=SCOPES
        )
        flow.redirect_uri = "https://ai-email-assistant-frontend-rajat.vercel.app/gmail/callback"

        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
        )

        # Save state in session
        request.session['oauth_state'] = state

        return Response({'auth_url': auth_url}, status=status.HTTP_200_OK)


class GmailOAuthCallbackView(APIView):
    """
    POST /api/auth/gmail/callback/
    Handles Gmail OAuth callback and saves tokens.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')

        if not code:
            return Response(
                {'error': 'Authorization code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        SCOPES = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
        ]

        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:5173/gmail/callback"],
                    }
                },
                scopes=SCOPES
            )
            flow.redirect_uri = "https://ai-email-assistant-frontend-rajat.vercel.app/gmail/callback"

            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Save tokens to user profile
            profile = request.user.profile
            profile.gmail_access_token = credentials.token
            profile.gmail_refresh_token = credentials.refresh_token or profile.gmail_refresh_token
            profile.save()

            return Response(
                {'message': 'Gmail connected successfully!'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Gmail OAuth error: {str(e)}")
            return Response(
                {'error': f'Failed to connect Gmail: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
            
class GmailStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            connected = bool(profile.gmail_access_token)
            return Response({
                'connected': connected,
                'email': request.user.email
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'connected': False
            }, status=status.HTTP_200_OK)