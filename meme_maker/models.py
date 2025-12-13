"""
Models for django-meme-maker.

This module contains two main models:
- MemeTemplate: Reusable meme template images with titles and tags
- Meme: User-created memes based on templates with text overlays

Image Generation Strategy (IMPORTANT):
--------------------------------------
We use a HYBRID approach for storing meme data:

1. TEXT OVERLAYS AS JSON: We store text positioning, styling, and content in a 
   JSONField (`text_overlays`). This allows:
   - Future editing of meme text without re-uploading
   - Flexible positioning (not just top/bottom)
   - Rich styling (fonts, colors, sizes, stroke)
   - CSS-based rendering for preview

2. PRE-GENERATED OUTPUT IMAGE: We also store a rendered composite image 
   (`generated_image`) that is created when the meme is saved. This allows:
   - Fast downloads without server-side rendering on each request
   - Consistent output across different browsers
   - Easy sharing with a direct image URL
   - Works even if Pillow isn't available (falls back to CSS overlay)

The generated image is created using Pillow when available. If Pillow fails
or isn't available, we fall back to serving the template with CSS text overlay.
"""

import json
import io
import uuid
from django.db import models
from django.urls import reverse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .conf import meme_maker_settings


def template_upload_path(instance, filename):
    """Generate upload path for meme template images."""
    upload_path = meme_maker_settings.UPLOAD_PATH
    if not upload_path.endswith('/'):
        upload_path += '/'
    return f'{upload_path}templates/{filename}'


def meme_upload_path(instance, filename):
    """Generate upload path for generated meme images."""
    upload_path = meme_maker_settings.UPLOAD_PATH
    if not upload_path.endswith('/'):
        upload_path += '/'
    return f'{upload_path}generated/{filename}'


class MemeTemplate(models.Model):
    """
    A reusable meme template image.
    
    Users can search templates by title and tags, then create memes from them.
    Templates can be uploaded by users or pre-seeded by admins.
    """
    image = models.ImageField(
        upload_to=template_upload_path,
        storage=default_storage,
        help_text="The template image"
    )
    title = models.CharField(
        max_length=200,
        help_text="Searchable title for the template"
    )
    # Tags stored as comma-separated string for simplicity and DB compatibility
    # This approach works with SQLite, PostgreSQL, MySQL, etc.
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags for searching (e.g., 'funny, reaction, cat')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meme Template'
        verbose_name_plural = 'Meme Templates'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('meme_maker:template_detail', kwargs={'pk': self.pk})
    
    def get_tags_list(self):
        """Return tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tags_from_list(self, tags_list):
        """Set tags from a list."""
        self.tags = ', '.join(tags_list)
    
    @classmethod
    def search(cls, query):
        """
        Search templates by title and tags.
        Uses icontains for database-agnostic case-insensitive search.
        """
        if not query:
            return cls.objects.all()
        
        from django.db.models import Q
        return cls.objects.filter(
            Q(title__icontains=query) | Q(tags__icontains=query)
        ).distinct()
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove the image file from storage."""
        image_path = self.image.name if self.image else None
        super().delete(*args, **kwargs)
        if image_path:
            try:
                default_storage.delete(image_path)
            except Exception:
                pass


class Meme(models.Model):
    """
    A user-created meme based on a template.
    
    Stores both the text overlay configuration (as JSON) and a pre-generated
    composite image for fast downloading.
    
    Text Overlay JSON Schema:
    {
        "overlays": [
            {
                "text": "Hello World",
                "position": "top" | "bottom" | "custom",
                "x": 50,           # percentage from left (0-100)
                "y": 10,           # percentage from top (0-100)
                "font_size": 48,   # in pixels
                "font_family": "Impact",
                "color": "#FFFFFF",
                "stroke_color": "#000000",
                "stroke_width": 2,
                "text_align": "center",
                "uppercase": true
            }
        ]
    }
    """
    # Link to template (nullable for backward compatibility with existing memes)
    template = models.ForeignKey(
        MemeTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='memes',
        help_text="The template this meme was created from"
    )
    
    # Legacy fields for backward compatibility
    # These are kept for existing memes that don't use templates
    image = models.ImageField(
        upload_to=meme_upload_path,
        storage=default_storage,
        null=True,
        blank=True,
        help_text="Legacy: Direct image upload (use template instead)"
    )
    top_text = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Legacy: Text at top (use text_overlays instead)"
    )
    bottom_text = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Legacy: Text at bottom (use text_overlays instead)"
    )
    
    # New fields for template-based memes
    text_overlays = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON containing text overlay configuration"
    )
    
    # Pre-generated composite image for fast downloads
    generated_image = models.ImageField(
        upload_to=meme_upload_path,
        storage=default_storage,
        null=True,
        blank=True,
        help_text="The final rendered meme image"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meme'
        verbose_name_plural = 'Memes'
    
    def __str__(self):
        if self.template:
            return f"Meme from '{self.template.title}' #{self.id}"
        text_preview = self.top_text or self.bottom_text or 'No text'
        return f"Meme {self.id} - {text_preview[:30]}..."
    
    def get_absolute_url(self):
        return reverse('meme_maker:meme_detail', kwargs={'pk': self.pk})
    
    def get_source_image(self):
        """Get the source image (template or direct upload)."""
        if self.template and self.template.image:
            return self.template.image
        return self.image
    
    def get_source_image_url(self):
        """Get URL for the source image."""
        source = self.get_source_image()
        if source:
            return source.url
        return None
    
    def get_display_image_url(self):
        """
        Get the best image URL for display.
        Prefers generated image, falls back to source.
        """
        if self.generated_image:
            return self.generated_image.url
        return self.get_source_image_url()
    
    def get_overlays(self):
        """Get text overlays as a list."""
        if isinstance(self.text_overlays, dict):
            return self.text_overlays.get('overlays', [])
        return []
    
    def set_overlays(self, overlays_list):
        """Set text overlays from a list."""
        self.text_overlays = {'overlays': overlays_list}
    
    def get_overlay_for_css(self):
        """
        Convert overlays to a format suitable for CSS rendering.
        This is used when serving memes without a generated image.
        """
        overlays = self.get_overlays()
        if not overlays:
            # Fall back to legacy top/bottom text
            result = []
            if self.top_text:
                result.append({
                    'text': self.top_text,
                    'position': 'top',
                    'style': 'top: 1rem;'
                })
            if self.bottom_text:
                result.append({
                    'text': self.bottom_text,
                    'position': 'bottom',
                    'style': 'bottom: 1rem;'
                })
            return result
        
        result = []
        for overlay in overlays:
            position = overlay.get('position', 'top')
            if position == 'top':
                style = 'top: 1rem;'
            elif position == 'bottom':
                style = 'bottom: 1rem;'
            else:
                x = overlay.get('x', 50)
                y = overlay.get('y', 50)
                style = f'top: {y}%; left: {x}%; transform: translate(-50%, -50%);'
            
            color = overlay.get('color', '#FFFFFF')
            stroke = overlay.get('stroke_color', '#000000')
            font_size = overlay.get('font_size', 48)
            
            result.append({
                'text': overlay.get('text', ''),
                'position': position,
                'style': style,
                'color': color,
                'stroke_color': stroke,
                'font_size': font_size,
            })
        
        return result
    
    def generate_image(self, save=True):
        """
        Generate the composite meme image using Pillow.
        
        This creates a new image with text overlays burned in.
        The generated image is saved to the generated_image field.
        
        Returns True if successful, False otherwise.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import os
        except ImportError:
            # Pillow not available, skip generation
            return False
        
        source_image = self.get_source_image()
        if not source_image:
            return False
        
        try:
            # Open the source image
            source_image.seek(0)
            img = Image.open(source_image)
            img = img.convert('RGBA')
            
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Get overlays
            overlays = self.get_overlays()
            if not overlays:
                # Use legacy text
                overlays = []
                if self.top_text:
                    overlays.append({
                        'text': self.top_text,
                        'position': 'top',
                        'color': '#FFFFFF',
                        'stroke_color': '#000000',
                        'uppercase': True
                    })
                if self.bottom_text:
                    overlays.append({
                        'text': self.bottom_text,
                        'position': 'bottom',
                        'color': '#FFFFFF',
                        'stroke_color': '#000000',
                        'uppercase': True
                    })
            
            # Try to load Impact font, fall back to default
            font_size = max(int(width / 10), 24)
            try:
                font = ImageFont.truetype("Impact", font_size)
            except (IOError, OSError):
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf", font_size)
                except (IOError, OSError):
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", font_size)
                    except (IOError, OSError):
                        font = ImageFont.load_default()
            
            for overlay in overlays:
                text = overlay.get('text', '')
                if not text:
                    continue
                
                if overlay.get('uppercase', True):
                    text = text.upper()
                
                # Calculate position
                position = overlay.get('position', 'top')
                
                # Get text bounding box
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (width - text_width) // 2
                
                if position == 'top':
                    y = int(height * 0.05)
                elif position == 'bottom':
                    y = height - text_height - int(height * 0.05)
                else:
                    x = int(width * overlay.get('x', 50) / 100) - text_width // 2
                    y = int(height * overlay.get('y', 50) / 100) - text_height // 2
                
                # Draw text with stroke
                stroke_color = overlay.get('stroke_color', '#000000')
                text_color = overlay.get('color', '#FFFFFF')
                stroke_width = overlay.get('stroke_width', 2)
                
                # Draw stroke (outline)
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
                
                # Draw main text
                draw.text((x, y), text, font=font, fill=text_color)
            
            # Save to buffer
            buffer = io.BytesIO()
            img_format = 'PNG' if img.mode == 'RGBA' else 'JPEG'
            img.save(buffer, format=img_format, quality=95)
            buffer.seek(0)
            
            # Generate filename
            ext = 'png' if img_format == 'PNG' else 'jpg'
            filename = f"meme_{self.pk or uuid.uuid4().hex}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # Save to field
            self.generated_image.save(filename, ContentFile(buffer.read()), save=save)
            
            return True
            
        except Exception as e:
            # Log error but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to generate meme image: {e}")
            return False
    
    def save(self, *args, **kwargs):
        """Override save to generate the composite image."""
        # First save to get a PK if new
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Generate composite image
        # Only regenerate if we have overlays or legacy text
        should_generate = (
            self.get_overlays() or 
            self.top_text or 
            self.bottom_text
        ) and self.get_source_image()
        
        if should_generate:
            # Generate but don't trigger another save loop
            self.generate_image(save=False)
            # Update just the generated_image field
            if self.generated_image:
                Meme.objects.filter(pk=self.pk).update(
                    generated_image=self.generated_image
                )
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove image files from storage."""
        image_path = self.image.name if self.image else None
        generated_path = self.generated_image.name if self.generated_image else None
        
        super().delete(*args, **kwargs)
        
        for path in [image_path, generated_path]:
            if path:
                try:
                    default_storage.delete(path)
                except Exception:
                    pass
