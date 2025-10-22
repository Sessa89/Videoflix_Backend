"""
Signal handlers for the Video app.

- On `post_save` (created=True): enqueue an async conversion task (example: 480p)
- On `post_delete`: remove the source file from disk if present

Notes:
- The example uses django-rq and a plain ffmpeg task for demonstration purposes.
- For production-grade pipelines, consider better error handling and idempotency.
"""

import os
import shutil
import logging
from pathlib import Path
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import django_rq

from .models import Video
from .tasks import transcode_to_hls

logger = logging.getLogger(__name__)

def _hls_dir_for(video_id: int) -> Path:
    root = Path(getattr(settings, 'HLS_ROOT', Path.cwd() / 'hls'))
    return root / str(video_id)

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    When a new Video is created, enqueue a background job to convert it.

    This keeps the HTTP request fast while media processing happens asynchronously.
    """

    if created and instance.video_file and getattr(instance.video_file, 'path', None):
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(
            transcode_to_hls,
            instance.pk,
            instance.video_file.path,
            resolutions=list(getattr(settings, 'HLS_ALLOWED_RESOLUTIONS', {'480p', '720p'})),
            seg_seconds=int(getattr(settings, 'HLS_SEGMENT_SECONDS', 6)),
        )

@receiver(post_delete, sender=Video)
def video_post_delete(sender, instance: Video, **kwargs):
    if instance.video_file and getattr(instance.video_file, 'path', None) and os.path.isfile(instance.video_file.path):
        os.remove(instance.video_file.path)

    if instance.thumbnail_image and getattr(instance.thumbnail_image, 'path', None) and os.path.isfile(instance.thumbnail_image.path):
        os.remove(instance.thumbnail_image.path)

    hls_dir = _hls_dir_for(instance.pk)
    if hls_dir.exists():
        shutil.rmtree(hls_dir)