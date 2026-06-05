from rest_framework import serializers


TONE_CHOICES = ['formal', 'friendly', 'concise', 'assertive', 'professional']


class ComposeEmailSerializer(serializers.Serializer):
    """
    Serializer for email composition request.
    User describes what email they want to write.
    """
    description = serializers.CharField(
        required=True,
        min_length=10,
        max_length=1000,
        error_messages={
            'required': 'Please describe what email you want to write.',
            'min_length': 'Description must be at least 10 characters.',
            'max_length': 'Description cannot exceed 1000 characters.',
        }
    )
    tone = serializers.ChoiceField(
        choices=TONE_CHOICES,
        default='professional'
    )
    recipient_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100
    )

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip()


class ImproveEmailSerializer(serializers.Serializer):
    """
    Serializer for email improvement request.
    User pastes their draft email to be improved.
    """
    draft = serializers.CharField(
        required=True,
        min_length=10,
        max_length=5000,
        error_messages={
            'required': 'Please provide your email draft.',
            'min_length': 'Draft must be at least 10 characters.',
            'max_length': 'Draft cannot exceed 5000 characters.',
        }
    )
    tone = serializers.ChoiceField(
        choices=TONE_CHOICES,
        default='professional'
    )

    def validate_draft(self, value):
        if not value.strip():
            raise serializers.ValidationError("Draft cannot be empty.")
        return value.strip()


class ReplyGeneratorSerializer(serializers.Serializer):
    """
    Serializer for reply generation request.
    User pastes the received email to generate a reply.
    """
    received_email = serializers.CharField(
        required=True,
        min_length=10,
        max_length=5000,
        error_messages={
            'required': 'Please provide the email you want to reply to.',
            'min_length': 'Email must be at least 10 characters.',
        }
    )
    tone = serializers.ChoiceField(
        choices=TONE_CHOICES,
        default='professional'
    )
    additional_context = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )


class SubjectGeneratorSerializer(serializers.Serializer):
    """
    Serializer for subject line generation.
    User provides email body to get subject suggestions.
    """
    email_body = serializers.CharField(
        required=True,
        min_length=10,
        max_length=5000,
        error_messages={
            'required': 'Please provide your email body.',
            'min_length': 'Email body must be at least 10 characters.',
        }
    )
    tone = serializers.ChoiceField(
        choices=TONE_CHOICES,
        default='professional'
    )


class SummarizeEmailSerializer(serializers.Serializer):
    """
    Serializer for email summarization.
    User provides long email to get a summary.
    """
    email_body = serializers.CharField(
        required=True,
        min_length=20,
        max_length=10000,
        error_messages={
            'required': 'Please provide the email to summarize.',
            'min_length': 'Email must be at least 20 characters to summarize.',
        }
    )