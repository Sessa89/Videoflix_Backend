"""
Admin configuration for the Video app.

Provides:
- A tabular listing with thumbnail preview
- Useful filters/search
- Bulk actions to set categories
"""

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import Video

# Register your models here.

class VideoAdminForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('thumbnail_image') and not cleaned.get('thumbnail_url'):
            raise forms.ValidationError("Please upload a thumbnail image or provide a thumbnail URL.")
        return cleaned

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Custom admin for Video entries.
    """

    list_display = ('id', 'title', 'category', 'created_at', 'thumbnail_preview')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'thumbnail_preview')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('title', 'description', 'category')}),
        ('Source', {'fields': ('video_file',)}),
        ('Artwork', {'fields': ('thumbnail_image', 'thumbnail_url', 'thumbnail_preview')}),
        ('Meta', {'fields': ('created_at',),}),
    )

    def _effective_thumb_url(self, obj):
        if obj.thumbnail_image:
            return obj.thumbnail_image.url
        if obj.thumbnail_url:
            return obj.thumbnail_url
        return None

    def thumbnail_preview(self, obj):
        """
        Render a small, rounded thumbnail preview in the admin.
        """

        url = self._effective_thumb_url(obj)

        if url:
            return format_html('<img src="{}"/>', url)
        return '-'
    thumbnail_preview.short_description = 'Thumbnail'

    @admin.action(description='Set category → Drama')
    def set_category_drama(self, request, queryset):
        """
        Bulk-set category to Drama.
        """

        queryset.update(category=Video.Category.DRAMA)

    @admin.action(description='Set category → Action')
    def set_category_action(self, request, queryset):
        """
        Bulk-set category to Action.
        """

        queryset.update(category=Video.Category.ACTION)

    @admin.action(description='Set category → Romance')
    def set_category_romance(self, request, queryset):
        """
        Bulk-set category to Romance.
        """

        queryset.update(category=Video.Category.ROMANCE)

    actions = ['set_category_drama', 'set_category_action', 'set_category_romance']