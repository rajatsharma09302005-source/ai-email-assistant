from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Email
from .serializers import (
    EmailListSerializer,
    EmailDetailSerializer,
    EmailCreateSerializer,
    EmailReplySerializer,
)
from gmail_integration.gmail_service import send_email_via_gmail, reply_to_email
from core.permissions import IsOwner

import logging

logger = logging.getLogger(__name__)


class EmailListView(APIView):
    """
    GET /api/emails/
    Returns list of all user's emails.
    Supports filtering by type: inbox, sent, drafts
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email_type = request.query_params.get('type', 'inbox')

        # Filter emails based on type
        if email_type == 'sent':
            emails = Email.objects.filter(
                user=request.user,
                is_sent=True,
                is_deleted=False
            )
        elif email_type == 'drafts':
            emails = Email.objects.filter(
                user=request.user,
                is_draft=True,
                is_sent=False,
                is_deleted=False
            )
        else:
            # Default: inbox (received emails)
            emails = Email.objects.filter(
                user=request.user,
                is_sent=False,
                is_deleted=False
            )

        serializer = EmailListSerializer(emails, many=True)
        return Response({
            'count': emails.count(),
            'emails': serializer.data
        }, status=status.HTTP_200_OK)


class EmailDetailView(APIView):
    """
    GET /api/emails/<id>/
    Returns single email details.
    Also marks email as read.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            email = Email.objects.get(pk=pk, user=request.user)

            # Mark as read when viewed
            if not email.is_read:
                email.is_read = True
                email.save()

            serializer = EmailDetailSerializer(email)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Email.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class EmailCreateView(APIView):
    """
    POST /api/emails/
    Create a draft email (not sent yet).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create draft email
        email = Email.objects.create(
            user=request.user,
            sender=request.user.email,
            recipient=serializer.validated_data['recipient'],
            cc=serializer.validated_data.get('cc', ''),
            bcc=serializer.validated_data.get('bcc', ''),
            subject=serializer.validated_data['subject'],
            body=serializer.validated_data['body'],
            is_draft=True,
            is_sent=False,
        )

        return Response(
            EmailDetailSerializer(email).data,
            status=status.HTTP_201_CREATED
        )


class EmailSendView(APIView):
    """
    POST /api/emails/<id>/send/
    Send a draft email via Gmail.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            email = Email.objects.get(pk=pk, user=request.user)
        except Email.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if email.is_sent:
            return Response(
                {'error': 'Email already sent'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has Gmail token
        if not hasattr(request.user, 'profile') or not request.user.profile.has_gmail_token():
            return Response(
                {'error': 'Gmail not connected. Please login with Gmail permissions.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get Gmail service
        from gmail_integration.gmail_service import get_gmail_service
        service = get_gmail_service(request.user.profile)

        if not service:
            return Response(
                {'error': 'Failed to connect to Gmail'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Send email via Gmail
        result = send_email_via_gmail(
            service=service,
            to=email.recipient,
            subject=email.subject,
            body=email.body,
            cc=email.cc,
            bcc=email.bcc,
        )

        if result:
            # Update email status
            email.is_sent = True
            email.is_draft = False
            email.sent_at = timezone.now()
            email.gmail_message_id = result.get('id', '')
            email.thread_id = result.get('threadId', '')
            email.save()

            return Response({
                'message': 'Email sent successfully',
                'email': EmailDetailSerializer(email).data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to send email via Gmail'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailReplyView(APIView):
    """
    POST /api/emails/<id>/reply/
    Reply to an existing email.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            original_email = Email.objects.get(pk=pk, user=request.user)
        except Email.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmailReplySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check Gmail token
        if not hasattr(request.user, 'profile') or not request.user.profile.has_gmail_token():
            return Response(
                {'error': 'Gmail not connected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get Gmail service
        from gmail_integration.gmail_service import get_gmail_service
        service = get_gmail_service(request.user.profile)

        if not service:
            return Response(
                {'error': 'Failed to connect to Gmail'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        body = serializer.validated_data['body']

        # Send reply via Gmail
        result = reply_to_email(
            service=service,
            thread_id=original_email.thread_id,
            message_id=original_email.gmail_message_id,
            to=original_email.sender,
            subject=original_email.subject,
            body=body,
        )

        if result:
            # Save reply as sent email
            reply = Email.objects.create(
                user=request.user,
                sender=request.user.email,
                recipient=original_email.sender,
                subject=f"Re: {original_email.subject}",
                body=body,
                thread_id=original_email.thread_id,
                in_reply_to=original_email.gmail_message_id,
                gmail_message_id=result.get('id', ''),
                is_sent=True,
                is_draft=False,
                sent_at=timezone.now(),
            )

            return Response({
                'message': 'Reply sent successfully',
                'email': EmailDetailSerializer(reply).data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to send reply'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailDeleteView(APIView):
    """
    DELETE /api/emails/<id>/
    Soft delete an email.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            email = Email.objects.get(pk=pk, user=request.user)
            email.is_deleted = True
            email.save()
            return Response(
                {'message': 'Email deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Email.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class EmailStarView(APIView):
    """
    POST /api/emails/<id>/star/
    Star or unstar an email.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            email = Email.objects.get(pk=pk, user=request.user)
            email.is_starred = not email.is_starred
            email.save()
            return Response({
                'message': 'Starred' if email.is_starred else 'Unstarred',
                'is_starred': email.is_starred
            }, status=status.HTTP_200_OK)
        except Email.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class EmailMarkReadView(APIView):
    """
    POST /api/emails/<id>/mark-read/
    Mark email as read or unread.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            email = Email.objects.get(pk=pk, user=request.user)
            email.is_read = not email.is_read
            email.save()
            return Response({
                'message': 'Marked as read' if email.is_read else 'Marked as unread',
                'is_read': email.is_read
            }, status=status.HTTP_200_OK)
        except Email.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )