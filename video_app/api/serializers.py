"""
Serializers for the Video app.

Exposes a lightweight serializer that maps model fields to an API-friendly
representation (human-readable category via `get_category_display`).
"""

from django.conf import settings
from rest_framework import serializers
from video_app.models import Video

class VideoListSerializer(serializers.ModelSerializer):
    """
    Read-only serializer used for list endpoints and simple detail views.
    """

    category = serializers.CharField(source='get_category_display', read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def get_thumbnail_url(self, obj):
        if obj.thumbnail_image:
            request = self.context.get('request')
            url = obj.thumbnail_image.url
            
            return request.build_absolute_uri(url) if request else url

        return None