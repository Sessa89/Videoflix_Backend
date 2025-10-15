"""
Database models for the Video app.

Currently exposes a single `Video` model which stores metadata and
optionally a raw uploaded file. Streaming (HLS) is handled via the file
system under `HLS_ROOT` in project settings.
"""

from django.db import models

# Create your models here.

class Video(models.Model):
    """
    Represents a movie/clip with metadata and optional uploaded video file.
    """

    class Category(models.TextChoices):
        ACTION = 'ACTION', 'Action'
        DRAMA = 'DRAMA', 'Drama'
        ROMANCE = 'ROMANCE', 'Romance'
        COMEDY = 'COMEDY', 'Comedy'
        THRILLER = 'THRILLER', 'Thriller'
        SCIFI = 'SCIFI', 'Scifi'
        DOC = 'DOC', 'Documentary'
        ANIMATION = 'ANIMATION', 'Animation'
        OTHER = 'OTHER', 'Other'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)

    thumbnail_url = models.URLField(max_length=500, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title