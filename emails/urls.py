from django.urls import path
from . import views

urlpatterns = [
    # List all emails - GET
    path('', views.EmailListView.as_view(), name='email-list'),

    # Create draft email - POST
    path('create/', views.EmailCreateView.as_view(), name='email-create'),

    # Get single email - GET
    path('<int:pk>/', views.EmailDetailView.as_view(), name='email-detail'),

    # Delete email - DELETE
    path('<int:pk>/delete/', views.EmailDeleteView.as_view(), name='email-delete'),

    # Send draft email - POST
    path('<int:pk>/send/', views.EmailSendView.as_view(), name='email-send'),

    # Reply to email - POST
    path('<int:pk>/reply/', views.EmailReplyView.as_view(), name='email-reply'),

    # Star/unstar email - POST
    path('<int:pk>/star/', views.EmailStarView.as_view(), name='email-star'),

    # Mark read/unread - POST
    path('<int:pk>/mark-read/', views.EmailMarkReadView.as_view(), name='email-mark-read'),
]