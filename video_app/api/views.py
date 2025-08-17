from django.conf import settings
from django.http import HttpResponse, FileResponse
from pathlib import Path
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from video_app.models import Video
from .serializers import VideoListSerializer

class VideoListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoListSerializer
    queryset = Video.objects.all()

class VideoIndexM3U8View(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id: int, resolution: str):
        allowed = getattr(settings, 'HLS_ALLOWED_RESOLUTIONS', None)
        if allowed and resolution not in allowed:
            return Response({'detail': 'Resolution not found.'}, status=status.HTTP_404_NOT_FOUND)

        root = Path(getattr(settings, 'HLS_ROOT', Path(__file__).resolve().parent.parent.parent / 'hls'))
        m3u8_path = root / str(movie_id) / resolution / 'index.m3u8'

        if not m3u8_path.exists():
            return Response({'detail': 'Video or manifest not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            content = m3u8_path.read_text(encoding='utf-8')
        except Exception:
            return Response({'detail': 'Could not read manifest.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return HttpResponse(content, content_type='application/vnd.apple.mpegurl')
    
class VideoSegmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id: int, resolution: str, segment: str):
        allowed_res = getattr(settings, 'HLS_ALLOWED_RESOLUTIONS', None)
        if allowed_res and resolution not in allowed_res:
            return Response({'detail': 'Video or segment not found.'}, status=status.HTTP_404_NOT_FOUND)

        if Path(segment).name != segment:
            return Response({'detail': 'Video or segment not found.'}, status=status.HTTP_404_NOT_FOUND)
        allowed_exts = getattr(settings, 'HLS_ALLOWED_SEGMENT_EXTS', {'.ts'})
        if Path(segment).suffix.lower() not in {ext.lower() for ext in allowed_exts}:
            return Response({'detail': 'Video or segment not found.'}, status=status.HTTP_404_NOT_FOUND)

        root = Path(getattr(settings, 'HLS_ROOT', Path(__file__).resolve().parent.parent.parent / 'hls'))
        seg_path = root / str(movie_id) / resolution / segment

        if not seg_path.exists():
            return Response({'detail': 'Video or segment not found.'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(seg_path, 'rb'), content_type='video/MP2T')