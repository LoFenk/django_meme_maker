"""
Admin configuration for django-meme-maker.

Provides admin interfaces for MemeTemplate, Meme, and Link models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import MemeTemplate, Meme, TemplateLink, MemeLink, TemplateFlag, MemeFlag, ExternalSourceQuery


@admin.register(MemeTemplate)
class MemeTemplateAdmin(admin.ModelAdmin):
    """Admin interface for meme templates."""
    
    list_display = ['id', 'title', 'image_preview', 'tags', 'nsfw', 'flagged', 'meme_count', 'created_at']
    list_filter = ['created_at', 'nsfw', 'flagged']
    search_fields = ['title', 'tags']
    readonly_fields = ['created_at', 'updated_at', 'flagged_at', 'image_preview_large']
    
    fieldsets = (
        (None, {
            'fields': ('image', 'title', 'tags', 'nsfw', 'flagged', 'flagged_at')
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
    
    list_display = ['id', 'template_title', 'meme_preview', 'overlay_preview', 'nsfw', 'flagged', 'created_at']
    list_filter = ['created_at', 'template', 'nsfw', 'flagged']
    search_fields = ['template__title']
    readonly_fields = ['created_at', 'updated_at', 'flagged_at', 'meme_preview_large', 'text_overlays_display']
    raw_id_fields = ['template']
    
    fieldsets = (
        (None, {
            'fields': ('template', 'nsfw', 'flagged', 'flagged_at')
        }),
        ('Legacy Image Upload', {
            'fields': ('image',),
            'classes': ('collapse',),
            'description': 'Only use if not using a template'
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
    
    def overlay_preview(self, obj):
        """Truncated overlay text for list display."""
        overlays = obj.get_overlays()
        if overlays:
            text = overlays[0].get('text', '')
            return text[:30] + ('...' if len(text) > 30 else '')
        return '-'
    overlay_preview.short_description = 'Text'
    
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


# =============================================================================
# LINK ADMIN CLASSES
# =============================================================================

class TemplateLinkInline(admin.TabularInline):
    """Inline admin for template links - shown on MemeTemplate detail page."""
    model = TemplateLink
    extra = 0
    readonly_fields = ['content_type', 'object_id', 'linked_object_display', 'link_type', 'created_at']
    fields = ['content_type', 'object_id', 'linked_object_display', 'link_type', 'created_at']
    
    def linked_object_display(self, obj):
        """Display the linked object."""
        if obj.linked_object:
            return str(obj.linked_object)
        return f"{obj.content_type.model}:{obj.object_id}"
    linked_object_display.short_description = 'Linked To'
    
    def has_add_permission(self, request, obj=None):
        return False  # Links should be created programmatically


class MemeLinkInline(admin.TabularInline):
    """Inline admin for meme links - shown on Meme detail page."""
    model = MemeLink
    extra = 0
    readonly_fields = ['content_type', 'object_id', 'linked_object_display', 'link_type', 'created_at']
    fields = ['content_type', 'object_id', 'linked_object_display', 'link_type', 'created_at']
    
    def linked_object_display(self, obj):
        """Display the linked object."""
        if obj.linked_object:
            return str(obj.linked_object)
        return f"{obj.content_type.model}:{obj.object_id}"
    linked_object_display.short_description = 'Linked To'
    
    def has_add_permission(self, request, obj=None):
        return False  # Links should be created programmatically


@admin.register(ExternalSourceQuery)
class ExternalSourceQueryAdmin(admin.ModelAdmin):
    """Admin interface for external search cache entries."""
    list_display = ['site_name', 'normalized_query', 'status', 'fetched_at', 'updated_at']
    list_filter = ['site_name', 'status', 'fetched_at']
    search_fields = ['query_str', 'normalized_query']
    readonly_fields = ['site_name', 'query_str', 'normalized_query', 'fetched_at', 'status', 'error_message', 'result_json', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('site_name', 'query_str', 'normalized_query', 'status', 'error_message')
        }),
        ('Result', {
            'fields': ('result_json',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('fetched_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(TemplateLink)
class TemplateLinkAdmin(admin.ModelAdmin):
    """Admin interface for template links."""
    
    list_display = ['id', 'template', 'content_type', 'object_id', 'link_type', 'created_at']
    list_filter = ['content_type', 'link_type', 'created_at']
    search_fields = ['template__title', 'link_type']
    readonly_fields = ['created_at']
    raw_id_fields = ['template']
    
    fieldsets = (
        (None, {
            'fields': ('template', 'content_type', 'object_id', 'link_type')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MemeLink)
class MemeLinkAdmin(admin.ModelAdmin):
    """Admin interface for meme links."""
    
    list_display = ['id', 'meme', 'content_type', 'object_id', 'link_type', 'created_at']
    list_filter = ['content_type', 'link_type', 'created_at']
    search_fields = ['meme__template__title', 'link_type']
    readonly_fields = ['created_at']
    raw_id_fields = ['meme']
    
    fieldsets = (
        (None, {
            'fields': ('meme', 'content_type', 'object_id', 'link_type')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TemplateFlag)
class TemplateFlagAdmin(admin.ModelAdmin):
    """Admin interface for template flags."""
    list_display = ['id', 'template', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['template__title', 'user__username']
    readonly_fields = ['created_at']
    raw_id_fields = ['template', 'user']


@admin.register(MemeFlag)
class MemeFlagAdmin(admin.ModelAdmin):
    """Admin interface for meme flags."""
    list_display = ['id', 'meme', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['meme__template__title', 'user__username']
    readonly_fields = ['created_at']
    raw_id_fields = ['meme', 'user']


# Add inlines to the main admin classes
MemeTemplateAdmin.inlines = [TemplateLinkInline]
MemeAdmin.inlines = [MemeLinkInline]
