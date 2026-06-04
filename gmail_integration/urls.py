from django.urls import path
from . import views

urlpatterns = [
    # Fetch inbox from Gmail - POST
    path('fetch-inbox/', views.FetchInboxView.as_view(), name='fetch-inbox'),

    # Fetch sent emails from Gmail - POST
    path('fetch-sent/', views.FetchSentView.as_view(), name='fetch-sent'),

    # Get email thread - GET
    path('thread/<str:thread_id>/', views.GetThreadView.as_view(), name='get-thread'),

    # Email statistics - GET
    path('stats/', views.GmailStatsView.as_view(), name='gmail-stats'),
]