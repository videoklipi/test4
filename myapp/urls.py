from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.process_video, name="process_video"),  # Updated to use process_video view
    path('playback_processed_video/', views.playback_processed_video, name='playback_processed_video'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)