"""
App configuration for the Video app.

The `ready()` hook imports signal handlers to ensure they are registered once
the app is loaded by Django.
"""

from django.apps import AppConfig

class VideoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        import video_app.signals
        
