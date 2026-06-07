from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Google OAuth login - POST
    path('google/', views.GoogleAuthView.as_view(), name='google-auth'),

    # Get current user details - GET
    path('user/', views.UserDetailView.as_view(), name='user-detail'),

    # Logout - POST
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Refresh JWT token - POST
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    path('gmail/init/', views.GmailOAuthInitView.as_view(), name='gmail-init'),
    path('gmail/callback/', views.GmailOAuthCallbackView.as_view(), name='gmail-callback'),
    
    # ✅ Gmail status check 
    path('gmail/status/', views.GmailStatusView.as_view(), name='gmail-status'),

]