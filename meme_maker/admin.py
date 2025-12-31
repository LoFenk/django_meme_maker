"""
Admin configuration for django-meme-maker.

Provides admin interfaces for MemeTemplate and Meme models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import MemeTemplate, Meme


@admin.register(MemeTemplate)
class MemeTemplateAdmin(admin.ModelAdmin):
    """Admin interface for meme templates."""
    
    list_display = ['id', 'title', 'image_preview', 'tags', 'meme_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'tags']
    readonly_fields = ['created_at', 'updated_at', 'image_preview_large']
    
    fieldsets = (
        (None, {
            'fields': ('image', 'title', 'tags')
        }),
        ('Preview', {
            'fields': ('image_preview_large',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Show a small image preview in the list."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover; border-radius: 4px;">',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        """Show a larger image preview in the detail view."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 100%; object-fit: contain; border-radius: 8px;">',
                obj.image.url
            )
        return '-'
    image_preview_large.short_description = 'Image Preview'
    
    def meme_count(self, obj):
        """Show count of memes created from this template."""
        return obj.memes.count()
    meme_count.short_description = 'Memes'


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    """Admin interface for memes."""
    
    list_display = ['id', 'template_title', 'meme_preview', 'top_text_preview', 'bottom_text_preview', 'created_at']
    list_filter = ['created_at', 'template']
    search_fields = ['top_text', 'bottom_text', 'template__title']
    readonly_fields = ['created_at', 'updated_at', 'meme_preview_large', 'text_overlays_display']
    raw_id_fields = ['template']
    
    fieldsets = (
        (None, {
            'fields': ('template',)
        }),
        ('Legacy Image Upload', {
            'fields': ('image',),
            'classes': ('collapse',),
            'description': 'Only use if not using a template'
        }),
        ('Text (Simple)', {
            'fields': ('top_text', 'bottom_text')
        }),
        ('Text Overlays (Advanced)', {
            'fields': ('text_overlays', 'text_overlays_display'),
            'classes': ('collapse',)
        }),
        ('Generated Output', {
            'fields': ('generated_image', 'meme_preview_large'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def template_title(self, obj):
        """Show template title."""
        if obj.template:
            return obj.template.title
        return '(Direct Upload)'
    template_title.short_description = 'Template'
    
    def meme_preview(self, obj):
        """Show a small meme preview in the list."""
        url = None
        if obj.generated_image:
            url = obj.generated_image.url
        elif obj.get_source_image():
            url = obj.get_source_image().url
        
        if url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover; border-radius: 4px;">',
                url
            )
        return '-'
    meme_preview.short_description = 'Preview'
    
    def meme_preview_large(self, obj):
        """Show a larger meme preview in the detail view."""
        url = None
        if obj.generated_image:
            url = obj.generated_image.url
        elif obj.get_source_image():
            url = obj.get_source_image().url
        
        if url:
            return format_html(
                '<img src="{}" style="max-height: 400px; max-width: 100%; object-fit: contain; border-radius: 8px;">',
                url
            )
        return '-'
    meme_preview_large.short_description = 'Meme Preview'
    
    def top_text_preview(self, obj):
        """Truncated top text for list display."""
        if obj.top_text:
            return obj.top_text[:30] + ('...' if len(obj.top_text) > 30 else '')
        return '-'
    top_text_preview.short_description = 'Top'
    
    def bottom_text_preview(self, obj):
        """Truncated bottom text for list display."""
        if obj.bottom_text:
            return obj.bottom_text[:30] + ('...' if len(obj.bottom_text) > 30 else '')
        return '-'
    bottom_text_preview.short_description = 'Bottom'
    
    def text_overlays_display(self, obj):
        """Display text overlays as formatted JSON."""
        import json
        if obj.text_overlays:
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">{}</pre>',
                json.dumps(obj.text_overlays, indent=2)
            )
        return '-'
    text_overlays_display.short_description = 'Text Overlays (Formatted)'
    
    actions = ['regenerate_images']
    
    @admin.action(description='Regenerate meme images')
    def regenerate_images(self, request, queryset):
        """Regenerate the composite images for selected memes."""
        count = 0
        for meme in queryset:
            if meme.generate_image(save=True):
                count += 1
        
        self.message_user(
            request,
            f'Successfully regenerated {count} of {queryset.count()} meme images.'
        )
