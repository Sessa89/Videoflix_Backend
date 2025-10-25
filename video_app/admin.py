"""
Admin configuration for the Video app.

Provides:
- A tabular listing with thumbnail preview
- Useful filters/search
- Bulk actions to set categories
"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import Video

# Register your models here.


class VideoAdminForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('title', 'description', 'category',
                  'video_file', 'thumbnail_image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['video_file'].required = True
        self.fields['thumbnail_image'].required = True

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Custom admin for Video entries.
    """

    form = VideoAdminForm

    list_display = ('id', 'title', 'category',
                    'created_at', 'thumbnail_preview')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'thumbnail_preview')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('title', 'description', 'category')}),
        ('Source', {'fields': ('video_file',)}),
        ('Artwork', {'fields': ('thumbnail_image', 'thumbnail_preview')}),
        ('Meta', {'fields': ('created_at',), }),
    )

    def thumbnail_preview(self, obj):
        """
        Render a small, rounded thumbnail preview in the admin.
        """

        if not obj:
            return '-'
        thumb = getattr(obj, 'thumbnail_image', None)
        try:
            if thumb and getattr(thumb, 'name', None):
                return format_html(
                    '<div style="width:140px; aspect-ratio:16/9; overflow:hidden; border-radius:8px;" >'
                        '<img src="{}" alt="" style="width:100%; height:100%; object-fit:cover; display:block;" />'
                    '</div>',
                    thumb.url)
        except Exception:
            pass
        return '-'
    thumbnail_preview.short_description = 'Thumbnail'

    @admin.action(description='Set category → Action')
    def set_category_action(self, request, queryset):
        """
        Bulk-set category to Action.
        """

        queryset.update(category=Video.Category.ACTION)

    @admin.action(description='Set category → Drama')
    def set_category_drama(self, request, queryset):
        """
        Bulk-set category to Drama.
        """

        queryset.update(category=Video.Category.DRAMA)

    @admin.action(description='Set category → Romance')
    def set_category_romance(self, request, queryset):
        """
        Bulk-set category to Romance.
        """

        queryset.update(category=Video.Category.ROMANCE)

    @admin.action(description='Set category → Comedy')
    def set_category_comedy(self, request, queryset):
        """
        Bulk-set category to Comedy.
        """

        queryset.update(category=Video.Category.COMEDY)

    @admin.action(description='Set category → Thriller')
    def set_category_thriller(self, request, queryset):
        """
        Bulk-set category to Thriller.
        """

        queryset.update(category=Video.Category.THRILLER)

    @admin.action(description='Set category → Scifi')
    def set_category_scifi(self, request, queryset):
        """
        Bulk-set category to Scifi.
        """

        queryset.update(category=Video.Category.SCIFI)

    @admin.action(description='Set category → Documentary')
    def set_category_documentary(self, request, queryset):
        """
        Bulk-set category to Documentary.
        """

        queryset.update(category=Video.Category.DOC)

    @admin.action(description='Set category → Animation')
    def set_category_animation(self, request, queryset):
        """
        Bulk-set category to Animation.
        """

        queryset.update(category=Video.Category.ANIMATION)

    @admin.action(description='Set category → Other')
    def set_category_other(self, request, queryset):
        """
        Bulk-set category to Other.
        """

        queryset.update(category=Video.Category.OTHER)

    actions = [
        'set_category_action', 'set_category_drama', 'set_category_romance',
        'set_category_comedy', 'set_category_thriller', 'set_category_scifi',
        'set_category_documentary', 'set_category_animation', 'set_category_other'
        ]
