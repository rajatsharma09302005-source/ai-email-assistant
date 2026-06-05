from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Auth endpoints
    path('api/auth/', include('users.urls')),

    # Email CRUD endpoints
    path('api/emails/', include('emails.urls')),

    # Gmail API endpoints
    path('api/gmail/', include('gmail_integration.urls')),

    # AI Assistant endpoints
    path('api/ai/', include('ai_assistant.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )