from django.urls import path
from . import views

urlpatterns = [
    # Compose new email - POST
    path('compose/', views.ComposeEmailView.as_view(), name='ai-compose'),

    # Improve existing email - POST
    path('improve/', views.ImproveEmailView.as_view(), name='ai-improve'),

    # Generate reply - POST
    path('reply/', views.ReplyGeneratorView.as_view(), name='ai-reply'),

    # Generate subject lines - POST
    path('subject/', views.SubjectGeneratorView.as_view(), name='ai-subject'),

    # Summarize email - POST
    path('summarize/', views.SummarizeEmailView.as_view(), name='ai-summarize'),

    # AI usage logs - GET
    path('logs/', views.AILogListView.as_view(), name='ai-logs'),
]