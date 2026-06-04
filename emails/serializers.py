from rest_framework import serializers
from .models import Email, AILog


class EmailListSerializer(serializers.ModelSerializer):
    """
    Serializer for email list view.
    Shows minimal fields for performance.
    """
    class Meta:
        model = Email
        fields = [
            'id',
            'sender',
            'recipient',
            'subject',
            'is_read',
            'is_sent',
            'is_starred',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EmailDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for single email detail view.
    Shows all fields including body.
    """
    class Meta:
        model = Email
        fields = [
            'id',
            'gmail_message_id',
            'thread_id',
            'sender',
            'recipient',
            'cc',
            'bcc',
            'subject',
            'body',
            'html_body',
            'is_read',
            'is_sent',
            'is_draft',
            'is_starred',
            'created_at',
            'sent_at',
        ]
        read_only_fields = ['id', 'gmail_message_id', 'thread_id', 'created_at']


class EmailCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/sending emails.
    """
    class Meta:
        model = Email
        fields = [
            'recipient',
            'cc',
            'bcc',
            'subject',
            'body',
        ]

    def validate_recipient(self, value):
        if not value:
            raise serializers.ValidationError("Recipient email is required.")
        return value

    def validate_subject(self, value):
        if not value:
            raise serializers.ValidationError("Subject is required.")
        return value

    def validate_body(self, value):
        if not value:
            raise serializers.ValidationError("Email body is required.")
        return value


class EmailReplySerializer(serializers.Serializer):
    """
    Serializer for replying to an email.
    """
    body = serializers.CharField(required=True)

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Reply body cannot be empty.")
        return value


class AILogSerializer(serializers.ModelSerializer):
    """
    Serializer for AI logs.
    """
    class Meta:
        model = AILog
        fields = [
            'id',
            'action',
            'tone',
            'input_text',
            'output_text',
            'success',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']