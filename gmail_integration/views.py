from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from emails.models import Email
from emails.serializers import EmailListSerializer
from .gmail_service import (
    get_gmail_service,
    fetch_inbox_emails,
    fetch_sent_emails,
    get_email_thread,
)

import logging

logger = logging.getLogger(__name__)


class FetchInboxView(APIView):
    """
    POST /api/gmail/fetch-inbox/
    Fetches emails from Gmail and saves to database.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if user has Gmail token
        if not hasattr(request.user, 'profile') or not request.user.profile.has_gmail_token():
            return Response(
                {'error': 'Gmail not connected. Please login with Gmail permissions.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get Gmail service
        service = get_gmail_service(request.user.profile)
        if not service:
            return Response(
                {'error': 'Failed to connect to Gmail API'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Fetch emails from Gmail
        max_results = request.data.get('max_results', 20)
        gmail_emails = fetch_inbox_emails(service, max_results=max_results)

        if not gmail_emails:
            return Response({
                'message': 'No emails found or failed to fetch',
                'count': 0,
                'emails': []
            }, status=status.HTTP_200_OK)

        # Save emails to database (avoid duplicates)
        saved_count = 0
        for email_data in gmail_emails:
            # Check if email already exists
            exists = Email.objects.filter(
                user=request.user,
                gmail_message_id=email_data['gmail_message_id']
            ).exists()

            if not exists and email_data['gmail_message_id']:
                Email.objects.create(
                    user=request.user,
                    gmail_message_id=email_data['gmail_message_id'],
                    thread_id=email_data.get('thread_id', ''),
                    sender=email_data.get('sender', ''),
                    recipient=email_data.get('recipient', request.user.email),
                    cc=email_data.get('cc', ''),
                    subject=email_data.get('subject', ''),
                    body=email_data.get('body', ''),
                    html_body=email_data.get('html_body', ''),
                    is_read=email_data.get('is_read', False),
                    is_sent=False,
                    is_draft=False,
                )
                saved_count += 1

        # Return updated inbox
        emails = Email.objects.filter(
            user=request.user,
            is_sent=False,
            is_deleted=False
        ).order_by('-created_at')

        serializer = EmailListSerializer(emails, many=True)

        return Response({
            'message': f'Fetched and saved {saved_count} new emails',
            'count': emails.count(),
            'emails': serializer.data
        }, status=status.HTTP_200_OK)


class FetchSentView(APIView):
    """
    POST /api/gmail/fetch-sent/
    Fetches sent emails from Gmail and saves to database.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'profile') or not request.user.profile.has_gmail_token():
            return Response(
                {'error': 'Gmail not connected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = get_gmail_service(request.user.profile)
        if not service:
            return Response(
                {'error': 'Failed to connect to Gmail API'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        max_results = request.data.get('max_results', 20)
        gmail_emails = fetch_sent_emails(service, max_results=max_results)

        saved_count = 0
        for email_data in gmail_emails:
            exists = Email.objects.filter(
                user=request.user,
                gmail_message_id=email_data['gmail_message_id']
            ).exists()

            if not exists and email_data['gmail_message_id']:
                Email.objects.create(
                    user=request.user,
                    gmail_message_id=email_data['gmail_message_id'],
                    thread_id=email_data.get('thread_id', ''),
                    sender=request.user.email,
                    recipient=email_data.get('recipient', ''),
                    subject=email_data.get('subject', ''),
                    body=email_data.get('body', ''),
                    is_sent=True,
                    is_draft=False,
                    is_read=True,
                )
                saved_count += 1

        emails = Email.objects.filter(
            user=request.user,
            is_sent=True,
            is_deleted=False
        ).order_by('-created_at')

        serializer = EmailListSerializer(emails, many=True)
        return Response({
            'message': f'Fetched {saved_count} sent emails',
            'count': emails.count(),
            'emails': serializer.data
        }, status=status.HTTP_200_OK)


class GetThreadView(APIView):
    """
    GET /api/gmail/thread/<thread_id>/
    Get full email conversation thread.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        if not hasattr(request.user, 'profile') or not request.user.profile.has_gmail_token():
            return Response(
                {'error': 'Gmail not connected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = get_gmail_service(request.user.profile)
        if not service:
            return Response(
                {'error': 'Failed to connect to Gmail API'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        thread_emails = get_email_thread(service, thread_id)
        return Response({
            'thread_id': thread_id,
            'count': len(thread_emails),
            'emails': thread_emails
        }, status=status.HTTP_200_OK)


class GmailStatsView(APIView):
    """
    GET /api/gmail/stats/
    Get email statistics for dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total_emails = Email.objects.filter(user=user, is_deleted=False).count()
        unread_emails = Email.objects.filter(user=user, is_read=False, is_deleted=False).count()
        sent_emails = Email.objects.filter(user=user, is_sent=True, is_deleted=False).count()
        starred_emails = Email.objects.filter(user=user, is_starred=True, is_deleted=False).count()

        return Response({
            'total': total_emails,
            'unread': unread_emails,
            'sent': sent_emails,
            'starred': starred_emails,
        }, status=status.HTTP_200_OK)