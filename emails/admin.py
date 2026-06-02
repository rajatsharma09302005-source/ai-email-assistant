from django.contrib import admin
from .models import Email, AILog

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'is_sent', 'created_at')
    list_filter = ('is_sent', 'is_read', 'created_at')
    search_fields = ('subject', 'sender', 'recipient')
    readonly_fields = ('gmail_message_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Email Information', {
            'fields': ('user', 'subject', 'sender', 'recipient', 'cc', 'bcc')
        }),
        ('Content', {
            'fields': ('body', 'html_body')
        }),
        ('Status', {
            'fields': ('is_sent', 'is_read', 'is_draft', 'is_starred')
        }),
        ('Gmail', {
            'fields': ('gmail_message_id', 'thread_id', 'in_reply_to'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AILog)
class AILogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'success', 'created_at')
    list_filter = ('action', 'success', 'created_at')
    search_fields = ('user__email', 'action')
    readonly_fields = ('created_at',)

