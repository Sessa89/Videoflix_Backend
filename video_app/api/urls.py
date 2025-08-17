from django.urls import path
from .views import VideoListView, VideoIndexM3U8View, VideoSegmentView

urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', VideoIndexM3U8View.as_view(), name='video-m3u8'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>/', VideoSegmentView.as_view(), name='video-segment'),
]
