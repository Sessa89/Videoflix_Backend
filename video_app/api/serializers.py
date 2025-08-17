from rest_framework import serializers
from video_app.models import Video

class VideoListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']