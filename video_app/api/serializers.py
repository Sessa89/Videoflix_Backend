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

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if instance.thumbnail_image:
            url = instance.thumbnail_image.url
            if request is not None:
                url = request.build_absolute_uri(url)
            data['thumbnail_url'] = url

        if not data.get('thumbnail_url'):
            data['thumbnail_url'] = getattr(settings, 'VIDEO_THUMBNAIL_PLACEHOLDER_URL', None)

        return data