"""
Serializers for the Video app.

Exposes a lightweight serializer that maps model fields to an API-friendly
representation (human-readable category via `get_category_display`).
"""

from rest_framework import serializers
from video_app.models import Video

class VideoListSerializer(serializers.ModelSerializer):
    """
    Read-only serializer used for list endpoints and simple detail views.
    """

    category = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']