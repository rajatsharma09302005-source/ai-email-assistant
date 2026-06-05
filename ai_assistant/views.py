from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from emails.models import AILog
from .serializers import (
    ComposeEmailSerializer,
    ImproveEmailSerializer,
    ReplyGeneratorSerializer,
    SubjectGeneratorSerializer,
    SummarizeEmailSerializer,
)
from .gemini_service import (
    compose_email,
    improve_email,
    generate_reply,
    generate_subject,
    summarize_email,
)

import logging

logger = logging.getLogger(__name__)


def save_ai_log(user, action, tone, input_text, output_text,
                processing_time=0.0, success=True, error_message=''):
    """
    Helper function to save AI request logs to database.
    """
    try:
        AILog.objects.create(
            user=user,
            action=action,
            tone=tone,
            input_text=input_text[:2000],   # Limit input length
            output_text=output_text[:5000],  # Limit output length
            processing_time=processing_time,
            success=success,
            error_message=error_message[:500] if error_message else '',
        )
    except Exception as e:
        logger.error(f"Failed to save AI log: {str(e)}")


class ComposeEmailView(APIView):
    """
    POST /api/ai/compose/

    Generate a complete email from a description.

    Request body:
    {
        "description": "Write an email to my manager requesting a day off",
        "tone": "formal",
        "recipient_name": "Mr. Smith"  (optional)
    }

    Response:
    {
        "subject": "Request for Day Off",
        "body": "Dear Mr. Smith, ...",
        "tone": "formal",
        "processing_time": 1.23
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ComposeEmailSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        description = serializer.validated_data['description']
        tone = serializer.validated_data['tone']
        recipient_name = serializer.validated_data.get('recipient_name', '')

        # Call Gemini API
        result = compose_email(
            description=description,
            tone=tone,
            recipient_name=recipient_name
        )

        if result:
            # Save to AI log
            save_ai_log(
                user=request.user,
                action='compose',
                tone=tone,
                input_text=description,
                output_text=f"Subject: {result.get('subject', '')}\n\n{result.get('body', '')}",
                processing_time=result.get('processing_time', 0.0),
                success=True,
            )

            return Response({
                'subject': result.get('subject', ''),
                'body': result.get('body', ''),
                'tone': tone,
                'processing_time': round(result.get('processing_time', 0.0), 2),
            }, status=status.HTTP_200_OK)

        else:
            # Save failed log
            save_ai_log(
                user=request.user,
                action='compose',
                tone=tone,
                input_text=description,
                output_text='',
                success=False,
                error_message='Gemini API failed to generate email',
            )

            return Response(
                {'error': 'Failed to generate email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImproveEmailView(APIView):
    """
    POST /api/ai/improve/

    Improve an existing email draft.

    Request body:
    {
        "draft": "hey can u send me the report asap thanks",
        "tone": "professional"
    }

    Response:
    {
        "subject": "Request for Report",
        "body": "Dear [Name], I hope this email finds you well...",
        "tone": "professional",
        "processing_time": 1.45
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ImproveEmailSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        draft = serializer.validated_data['draft']
        tone = serializer.validated_data['tone']

        # Call Gemini API
        result = improve_email(draft=draft, tone=tone)

        if result:
            save_ai_log(
                user=request.user,
                action='improve',
                tone=tone,
                input_text=draft,
                output_text=f"Subject: {result.get('subject', '')}\n\n{result.get('body', '')}",
                processing_time=result.get('processing_time', 0.0),
                success=True,
            )

            return Response({
                'subject': result.get('subject', ''),
                'body': result.get('body', ''),
                'original': draft,
                'tone': tone,
                'processing_time': round(result.get('processing_time', 0.0), 2),
            }, status=status.HTTP_200_OK)

        else:
            save_ai_log(
                user=request.user,
                action='improve',
                tone=tone,
                input_text=draft,
                output_text='',
                success=False,
                error_message='Gemini API failed to improve email',
            )

            return Response(
                {'error': 'Failed to improve email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReplyGeneratorView(APIView):
    """
    POST /api/ai/reply/

    Generate a smart reply to a received email.

    Request body:
    {
        "received_email": "Hi, can we schedule a meeting tomorrow?",
        "tone": "friendly",
        "additional_context": "I am available in the afternoon"
    }

    Response:
    {
        "subject": "Re: Meeting Request",
        "body": "Hi, Thank you for reaching out...",
        "tone": "friendly",
        "processing_time": 1.12
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReplyGeneratorSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        received_email = serializer.validated_data['received_email']
        tone = serializer.validated_data['tone']
        additional_context = serializer.validated_data.get('additional_context', '')

        # Call Gemini API
        result = generate_reply(
            received_email=received_email,
            tone=tone,
            additional_context=additional_context
        )

        if result:
            save_ai_log(
                user=request.user,
                action='reply',
                tone=tone,
                input_text=received_email,
                output_text=f"Subject: {result.get('subject', '')}\n\n{result.get('body', '')}",
                processing_time=result.get('processing_time', 0.0),
                success=True,
            )

            return Response({
                'subject': result.get('subject', ''),
                'body': result.get('body', ''),
                'tone': tone,
                'processing_time': round(result.get('processing_time', 0.0), 2),
            }, status=status.HTTP_200_OK)

        else:
            save_ai_log(
                user=request.user,
                action='reply',
                tone=tone,
                input_text=received_email,
                output_text='',
                success=False,
                error_message='Gemini API failed to generate reply',
            )

            return Response(
                {'error': 'Failed to generate reply. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubjectGeneratorView(APIView):
    """
    POST /api/ai/subject/

    Generate subject line suggestions for an email.

    Request body:
    {
        "email_body": "I wanted to follow up on our last meeting...",
        "tone": "professional"
    }

    Response:
    {
        "subjects": [
            "Following Up on Our Meeting",
            "Next Steps from Our Discussion",
            ...
        ],
        "tone": "professional",
        "processing_time": 0.98
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubjectGeneratorSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        email_body = serializer.validated_data['email_body']
        tone = serializer.validated_data['tone']

        # Call Gemini API
        result = generate_subject(email_body=email_body, tone=tone)

        if result:
            save_ai_log(
                user=request.user,
                action='subject',
                tone=tone,
                input_text=email_body,
                output_text=', '.join(result.get('subjects', [])),
                processing_time=result.get('processing_time', 0.0),
                success=True,
            )

            return Response({
                'subjects': result.get('subjects', []),
                'tone': tone,
                'processing_time': round(result.get('processing_time', 0.0), 2),
            }, status=status.HTTP_200_OK)

        else:
            save_ai_log(
                user=request.user,
                action='subject',
                tone=tone,
                input_text=email_body,
                output_text='',
                success=False,
                error_message='Gemini API failed to generate subjects',
            )

            return Response(
                {'error': 'Failed to generate subjects. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SummarizeEmailView(APIView):
    """
    POST /api/ai/summarize/

    Summarize a long email into key points.

    Request body:
    {
        "email_body": "Long email text here..."
    }

    Response:
    {
        "summary": "The email discusses...",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "action_items": ["Action 1"],
        "processing_time": 1.05
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SummarizeEmailSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        email_body = serializer.validated_data['email_body']

        # Call Gemini API
        result = summarize_email(email_body=email_body)

        if result:
            save_ai_log(
                user=request.user,
                action='summarize',
                tone='professional',
                input_text=email_body,
                output_text=result.get('summary', ''),
                processing_time=result.get('processing_time', 0.0),
                success=True,
            )

            return Response({
                'summary': result.get('summary', ''),
                'key_points': result.get('key_points', []),
                'action_items': result.get('action_items', []),
                'processing_time': round(result.get('processing_time', 0.0), 2),
            }, status=status.HTTP_200_OK)

        else:
            save_ai_log(
                user=request.user,
                action='summarize',
                tone='professional',
                input_text=email_body,
                output_text='',
                success=False,
                error_message='Gemini API failed to summarize',
            )

            return Response(
                {'error': 'Failed to summarize email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AILogListView(APIView):
    """
    GET /api/ai/logs/
    Get user's AI usage history.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = AILog.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]

        from emails.serializers import AILogSerializer
        serializer = AILogSerializer(logs, many=True)

        return Response({
            'count': logs.count(),
            'logs': serializer.data
        }, status=status.HTTP_200_OK)