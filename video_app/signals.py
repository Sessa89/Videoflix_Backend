"""
Signal handlers for the Video app.

- On `post_save` (created=True): enqueue an async conversion task (example: 480p)
- On `post_delete`: remove the source file from disk if present

Notes:
- The example uses django-rq and a plain ffmpeg task for demonstration purposes.
- For production-grade pipelines, consider better error handling and idempotency.
"""

from video_app.tasks import convert_480p
from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import os
import django_rq

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    When a new Video is created, enqueue a background job to convert it.

    This keeps the HTTP request fast while media processing happens asynchronously.
    """

    print('Video wurde gespeichert')
    if created:
        print('New video created')
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(convert_480p, instance.video_file.path)


@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Clean up the source file from the filesystem after the DB row is deleted.

    Important: if you use cloud storage, replace this with the appropriate SDK call.
    """
    
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)

