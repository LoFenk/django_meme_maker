"""
Models for django-meme-maker.

This module contains the following models:
- MemeTemplate: Reusable meme template images with titles and tags
- Meme: User-created memes based on templates with text overlays
- TemplateRating: Star ratings for templates
- MemeRating: Star ratings for memes
- TemplateLink: Generic many-to-many linking templates to any object
- MemeLink: Generic many-to-many linking memes to any object

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

Rating System:
--------------
Both templates and memes support 1-5 star ratings. Ratings are tracked per
session to prevent duplicate voting while not requiring authentication.

Object Linking System:
----------------------
Both templates and memes can be linked to ANY object in your project using
Django's ContentTypes framework. This provides a generic many-to-many relationship.

Usage:
    # Link to objects
    meme.link_to(product)
    meme.link_to(blog_post)
    template.link_to(campaign)
    
    # Query linked objects
    meme.get_linked_objects()
    meme.is_linked_to(product)
    
    # Query by linked object
    Meme.objects.linked_to(product)
    MemeTemplate.objects.linked_to(campaign)
"""

import json
import io
import uuid
from django.db import models
from django.urls import reverse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .conf import meme_maker_settings


# =============================================================================
# CUSTOM MANAGERS WITH LINKING SUPPORT
# =============================================================================

class LinkableManager(models.Manager):
    """
    Custom manager that adds linked_to() queryset method.
    
    Usage:
        Meme.objects.linked_to(my_product)
        MemeTemplate.objects.linked_to(my_campaign)
    """
    
    def linked_to(self, obj):
        """
        Return all instances linked to the given object.
        
        Args:
            obj: Any Django model instance
            
        Returns:
            QuerySet of instances linked to obj
        """
        content_type = ContentType.objects.get_for_model(obj)
        # Get the related link model name (e.g., 'object_links')
        link_model = self.model._meta.get_field('object_links').related_model
        linked_ids = link_model.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        ).values_list(self._get_fk_field_name(), flat=True)
        return self.filter(pk__in=linked_ids)
    
    def _get_fk_field_name(self):
        """Get the FK field name in the link model (meme_id or template_id)."""
        # This will be overridden by subclasses
        raise NotImplementedError


class MemeManager(LinkableManager):
    """Manager for Meme model with linking support."""
    
    def _get_fk_field_name(self):
        return 'meme_id'


class MemeTemplateManager(LinkableManager):
    """Manager for MemeTemplate model with linking support."""
    
    def _get_fk_field_name(self):
        return 'template_id'


# =============================================================================
# MIXIN FOR LINKING FUNCTIONALITY
# =============================================================================

class LinkableMixin:
    """
    Mixin providing object linking functionality.
    
    Classes using this mixin should have an 'object_links' reverse relation
    to their corresponding Link model (TemplateLink or MemeLink).
    """
    
    def link_to(self, obj, **extra_fields):
        """
        Link this instance to another object.
        
        Args:
            obj: Any Django model instance to link to
            **extra_fields: Optional extra fields for the link (e.g., link_type, metadata)
            
        Returns:
            The created link instance, or existing one if already linked
            
        Example:
            meme.link_to(product)
            template.link_to(campaign, link_type='featured')
        """
        content_type = ContentType.objects.get_for_model(obj)
        link_model = self._meta.get_field('object_links').related_model
        
        # Get the FK field name for this model
        fk_field = 'meme' if hasattr(link_model, 'meme') else 'template'
        
        link, created = link_model.objects.get_or_create(
            **{fk_field: self},
            content_type=content_type,
            object_id=obj.pk,
            defaults=extra_fields
        )
        return link
    
    def unlink_from(self, obj):
        """
        Remove link to another object.
        
        Args:
            obj: The object to unlink from
            
        Returns:
            True if link was removed, False if it didn't exist
        """
        content_type = ContentType.objects.get_for_model(obj)
        link_model = self._meta.get_field('object_links').related_model
        fk_field = 'meme' if hasattr(link_model, 'meme') else 'template'
        
        deleted, _ = link_model.objects.filter(
            **{fk_field: self},
            content_type=content_type,
            object_id=obj.pk
        ).delete()
        return deleted > 0
    
    def is_linked_to(self, obj):
        """
        Check if this instance is linked to an object.
        
        Args:
            obj: The object to check
            
        Returns:
            True if linked, False otherwise
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.object_links.filter(
            content_type=content_type,
            object_id=obj.pk
        ).exists()
    
    def get_linked_objects(self, model_class=None):
        """
        Get all objects this instance is linked to.
        
        Args:
            model_class: Optional - filter to only return objects of this model type
            
        Returns:
            List of linked objects
            
        Example:
            meme.get_linked_objects()  # All linked objects
            meme.get_linked_objects(Product)  # Only linked Products
        """
        links = self.object_links.all()
        
        if model_class:
            content_type = ContentType.objects.get_for_model(model_class)
            links = links.filter(content_type=content_type)
        
        return [link.linked_object for link in links if link.linked_object]
    
    def get_links(self, model_class=None):
        """
        Get link instances (for accessing link metadata like link_type).
        
        Args:
            model_class: Optional - filter to only return links to this model type
            
        Returns:
            QuerySet of link instances
        """
        links = self.object_links.all()
        
        if model_class:
            content_type = ContentType.objects.get_for_model(model_class)
            links = links.filter(content_type=content_type)
        
        return links


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


class RatingMixin:
    """
    Mixin providing rating functionality.
    
    Classes using this mixin should have:
    - rating_sum: IntegerField for sum of all ratings
    - rating_count: IntegerField for number of ratings
    """
    
    def get_average_rating(self):
        """Calculate and return the average rating (0-5)."""
        if self.rating_count == 0:
            return 0
        return round(self.rating_sum / self.rating_count, 1)
    
    def get_rating_display(self):
        """Return rating as a display string."""
        avg = self.get_average_rating()
        if self.rating_count == 0:
            return "No ratings yet"
        return f"{avg}/5 ({self.rating_count} vote{'s' if self.rating_count != 1 else ''})"
    
    def add_rating(self, stars):
        """
        Add a new rating.
        
        Args:
            stars: Integer 1-5
        
        Returns:
            The new average rating
        """
        if not 1 <= stars <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        self.rating_sum += stars
        self.rating_count += 1
        self.save(update_fields=['rating_sum', 'rating_count'])
        return self.get_average_rating()
    
    def update_rating(self, old_stars, new_stars):
        """
        Update an existing rating.
        
        Args:
            old_stars: The previous rating value
            new_stars: The new rating value
        
        Returns:
            The new average rating
        """
        if not 1 <= new_stars <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        self.rating_sum = self.rating_sum - old_stars + new_stars
        self.save(update_fields=['rating_sum', 'rating_count'])
        return self.get_average_rating()


class MemeTemplate(LinkableMixin, RatingMixin, models.Model):
    """
    A reusable meme template image.
    
    Users can search templates by title and tags, then create memes from them.
    Templates can be uploaded by users or pre-seeded by admins.
    
    Linking:
        template.link_to(campaign)  # Link to any object
        template.get_linked_objects()  # Get all linked objects
        MemeTemplate.objects.linked_to(campaign)  # Query by linked object
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
    
    # Rating fields
    rating_sum = models.PositiveIntegerField(
        default=0,
        help_text="Sum of all ratings (for calculating average)"
    )
    rating_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of ratings received"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager with linked_to() support
    objects = MemeTemplateManager()
    
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
    def search(cls, query, order_by=None):
        """
        Search templates by title and tags.
        Uses icontains for database-agnostic case-insensitive search.
        
        Args:
            query: Search string
            order_by: Optional ordering ('rating', '-rating', 'created', '-created', 'title')
        """
        if query:
            from django.db.models import Q
            qs = cls.objects.filter(
                Q(title__icontains=query) | Q(tags__icontains=query)
            ).distinct()
        else:
            qs = cls.objects.all()
        
        # Apply ordering
        if order_by == 'rating' or order_by == '-rating':
            # Order by average rating (rating_sum / rating_count)
            # Handle division by zero by using Case/When
            from django.db.models import Case, When, F, FloatField, Value
            from django.db.models.functions import Cast
            
            qs = qs.annotate(
                avg_rating=Case(
                    When(rating_count=0, then=Value(0.0)),
                    default=Cast(F('rating_sum'), FloatField()) / Cast(F('rating_count'), FloatField()),
                    output_field=FloatField()
                )
            )
            if order_by == '-rating':
                qs = qs.order_by('-avg_rating', '-rating_count', '-created_at')
            else:
                qs = qs.order_by('avg_rating', 'rating_count', 'created_at')
        elif order_by == 'created':
            qs = qs.order_by('created_at')
        elif order_by == '-created':
            qs = qs.order_by('-created_at')
        elif order_by == 'title':
            qs = qs.order_by('title')
        elif order_by == '-title':
            qs = qs.order_by('-title')
        
        return qs
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove the image file from storage."""
        image_path = self.image.name if self.image else None
        super().delete(*args, **kwargs)
        if image_path:
            try:
                default_storage.delete(image_path)
            except Exception:
                pass


class Meme(LinkableMixin, RatingMixin, models.Model):
    """
    A user-created meme based on a template.
    
    Stores both the text overlay configuration (as JSON) and a pre-generated
    composite image for fast downloading.
    
    Linking:
        meme.link_to(product)  # Link to any object
        meme.link_to(user)  # Link to user
        meme.get_linked_objects()  # Get all linked objects
        Meme.objects.linked_to(product)  # Query by linked object
    
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
    
    # Rating fields
    rating_sum = models.PositiveIntegerField(
        default=0,
        help_text="Sum of all ratings (for calculating average)"
    )
    rating_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of ratings received"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager with linked_to() support
    objects = MemeManager()
    
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
    
    def generate_image(self):
        """
        Generate the composite meme image using Pillow.
        
        This creates a new image with text overlays burned in.
        The generated image is saved to the generated_image field.
        
        Returns the filename if successful, None otherwise.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # Pillow not available, skip generation
            return None
        
        source_image = self.get_source_image()
        if not source_image:
            return None
        
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
                        'uppercase': True,
                        'font_size': 48,
                    })
                if self.bottom_text:
                    overlays.append({
                        'text': self.bottom_text,
                        'position': 'bottom',
                        'color': '#FFFFFF',
                        'stroke_color': '#000000',
                        'uppercase': True,
                        'font_size': 48,
                    })
            
            # Font loading helper
            def load_font(size):
                """Try to load Impact font at given size, fall back to default."""
                font_paths = [
                    "Impact",
                    "/System/Library/Fonts/Supplemental/Impact.ttf",  # macOS
                    "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",  # Linux
                    "/usr/share/fonts/TTF/impact.ttf",  # Arch Linux
                    "C:\\Windows\\Fonts\\impact.ttf",  # Windows
                ]
                for font_path in font_paths:
                    try:
                        return ImageFont.truetype(font_path, size)
                    except (IOError, OSError):
                        continue
                # Fall back to default font
                return ImageFont.load_default()
            
            for overlay in overlays:
                text = overlay.get('text', '')
                if not text:
                    continue
                
                if overlay.get('uppercase', True):
                    text = text.upper()
                
                # Get user-specified font size, scale it relative to image width
                # User's font size is based on ~800px preview, scale to actual image
                user_font_size = overlay.get('font_size') or 48  # Handle None values
                scale_factor = width / 800.0
                font_size = max(16, int(user_font_size * scale_factor))
                
                # Load font at the correct size for this overlay
                font = load_font(font_size)
                
                # Calculate position
                position = overlay.get('position', 'top')
                
                # Get text bounding box
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (width - text_width) // 2
                
                if position == 'top':
                    y = int(height * 0.03)
                elif position == 'bottom':
                    y = height - text_height - int(height * 0.03)
                else:
                    x = int(width * overlay.get('x', 50) / 100) - text_width // 2
                    y = int(height * overlay.get('y', 50) / 100) - text_height // 2
                
                # Draw text with stroke
                stroke_color = overlay.get('stroke_color') or '#000000'  # Handle empty/None
                text_color = overlay.get('color') or '#FFFFFF'  # Handle empty/None
                # Scale stroke width with font size
                stroke_width = max(2, int(font_size / 16))
                
                # Draw stroke (outline) - use a more efficient method
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx * dx + dy * dy <= stroke_width * stroke_width:
                            draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
                
                # Draw main text
                draw.text((x, y), text, font=font, fill=text_color)
            
            # Apply watermark if configured
            img = self._apply_watermark(img)
            
            # Save to buffer
            buffer = io.BytesIO()
            # Convert to RGB for JPEG (no alpha channel)
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                img = background
            
            img.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)
            
            # Generate filename
            filename = f"meme_{self.pk or uuid.uuid4().hex}_{uuid.uuid4().hex[:8]}.jpg"
            
            # Return the filename and content for the caller to save
            return (filename, ContentFile(buffer.read()))
            
        except Exception as e:
            # Log error but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to generate meme image: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            return None
    
    def _apply_watermark(self, img):
        """
        Apply watermark to the image if WATERMARK_IMAGE is configured.
        
        The watermark is placed in the bottom-right corner with configurable
        opacity, scale, and padding.
        
        Args:
            img: PIL Image object (RGBA mode)
            
        Returns:
            PIL Image object with watermark applied (or unchanged if no watermark)
        """
        from PIL import Image
        import os
        
        watermark_path = meme_maker_settings.WATERMARK_IMAGE
        if not watermark_path:
            return img
        
        try:
            # Try to find the watermark file
            watermark_img = None
            
            # If it's an absolute path, use it directly
            if os.path.isabs(watermark_path) and os.path.exists(watermark_path):
                watermark_img = Image.open(watermark_path)
            else:
                # Try to find in static files
                from django.contrib.staticfiles import finders
                found_path = finders.find(watermark_path)
                if found_path:
                    watermark_img = Image.open(found_path)
                else:
                    # Try relative to BASE_DIR if available
                    from django.conf import settings as django_settings
                    if hasattr(django_settings, 'BASE_DIR'):
                        full_path = os.path.join(django_settings.BASE_DIR, watermark_path)
                        if os.path.exists(full_path):
                            watermark_img = Image.open(full_path)
            
            if not watermark_img:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Watermark image not found: {watermark_path}")
                return img
            
            # Ensure watermark has alpha channel
            watermark_img = watermark_img.convert('RGBA')
            
            # Get settings
            opacity = meme_maker_settings.WATERMARK_OPACITY
            scale = meme_maker_settings.WATERMARK_SCALE
            padding = meme_maker_settings.WATERMARK_PADDING
            
            # Calculate new watermark size (based on meme width)
            img_width, img_height = img.size
            wm_width, wm_height = watermark_img.size
            
            # Scale watermark to be a percentage of the meme width
            new_wm_width = int(img_width * scale)
            aspect_ratio = wm_height / wm_width
            new_wm_height = int(new_wm_width * aspect_ratio)
            
            # Resize watermark
            watermark_img = watermark_img.resize(
                (new_wm_width, new_wm_height), 
                Image.LANCZOS
            )
            
            # Apply opacity to watermark
            if opacity < 1.0:
                # Adjust alpha channel
                r, g, b, a = watermark_img.split()
                a = a.point(lambda x: int(x * opacity))
                watermark_img = Image.merge('RGBA', (r, g, b, a))
            
            # Calculate position (bottom-right with padding)
            x = img_width - new_wm_width - padding
            y = img_height - new_wm_height - padding
            
            # Composite watermark onto image
            img.paste(watermark_img, (x, y), watermark_img)
            
            return img
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to apply watermark: {e}")
            return img
    
    def save(self, *args, **kwargs):
        """Override save to generate the composite image."""
        # First save to get a PK if new
        super().save(*args, **kwargs)
        
        # Generate composite image
        # Only regenerate if we have overlays or legacy text
        should_generate = (
            self.get_overlays() or 
            self.top_text or 
            self.bottom_text
        ) and self.get_source_image()
        
        if should_generate:
            result = self.generate_image()
            if result:
                filename, content = result
                # Save the generated image directly to storage
                # and update the field using a direct DB update to avoid recursion
                from django.core.files.storage import default_storage
                
                # Determine the full path
                upload_path = meme_upload_path(self, filename)
                
                # Save to storage
                saved_path = default_storage.save(upload_path, content)
                
                # Update the model field directly in DB
                Meme.objects.filter(pk=self.pk).update(generated_image=saved_path)
    
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


# =============================================================================
# RATING TRACKING MODELS
# =============================================================================

class TemplateRating(models.Model):
    """
    Tracks individual ratings for templates.
    
    Uses session key to prevent duplicate ratings without requiring authentication.
    """
    template = models.ForeignKey(
        MemeTemplate,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    session_key = models.CharField(
        max_length=40,
        help_text="Session key to track who rated"
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating value 1-5"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('template', 'session_key')
        verbose_name = 'Template Rating'
        verbose_name_plural = 'Template Ratings'
    
    def __str__(self):
        return f"{self.template.title} - {self.stars} stars"


class MemeRating(models.Model):
    """
    Tracks individual ratings for memes.
    
    Uses session key to prevent duplicate ratings without requiring authentication.
    """
    meme = models.ForeignKey(
        Meme,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    session_key = models.CharField(
        max_length=40,
        help_text="Session key to track who rated"
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating value 1-5"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('meme', 'session_key')
        verbose_name = 'Meme Rating'
        verbose_name_plural = 'Meme Ratings'
    
    def __str__(self):
        return f"Meme #{self.meme.pk} - {self.stars} stars"


# =============================================================================
# OBJECT LINKING MODELS (Generic Many-to-Many)
# =============================================================================

class TemplateLink(models.Model):
    """
    Links a MemeTemplate to any object in your project.
    
    This enables a generic many-to-many relationship where templates
    can be tagged/linked to Products, Campaigns, Users, or any model.
    
    Usage:
        # From the template
        template.link_to(campaign)
        template.link_to(brand)
        template.get_linked_objects()
        
        # Query templates by linked object
        MemeTemplate.objects.linked_to(campaign)
    """
    template = models.ForeignKey(
        MemeTemplate,
        on_delete=models.CASCADE,
        related_name='object_links',
        help_text="The template being linked"
    )
    
    # GenericForeignKey to link to ANY model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object being linked to"
    )
    object_id = models.PositiveIntegerField(
        help_text="The ID of the object being linked to"
    )
    linked_object = GenericForeignKey('content_type', 'object_id')
    
    # Optional metadata for the link
    link_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional: categorize the link (e.g., 'featured', 'owned_by', 'related_to')"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional: additional data about this link"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('template', 'content_type', 'object_id')
        verbose_name = 'Template Link'
        verbose_name_plural = 'Template Links'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.template.title} → {self.content_type.model}:{self.object_id}"


class MemeLink(models.Model):
    """
    Links a Meme to any object in your project.
    
    This enables a generic many-to-many relationship where memes
    can be tagged/linked to Products, Users, Posts, or any model.
    
    Usage:
        # From the meme
        meme.link_to(product)
        meme.link_to(user)
        meme.get_linked_objects()
        
        # Query memes by linked object
        Meme.objects.linked_to(product)
    """
    meme = models.ForeignKey(
        Meme,
        on_delete=models.CASCADE,
        related_name='object_links',
        help_text="The meme being linked"
    )
    
    # GenericForeignKey to link to ANY model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object being linked to"
    )
    object_id = models.PositiveIntegerField(
        help_text="The ID of the object being linked to"
    )
    linked_object = GenericForeignKey('content_type', 'object_id')
    
    # Optional metadata for the link
    link_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional: categorize the link (e.g., 'created_by', 'featured_in', 'related_to')"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional: additional data about this link"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('meme', 'content_type', 'object_id')
        verbose_name = 'Meme Link'
        verbose_name_plural = 'Meme Links'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"Meme #{self.meme.pk} → {self.content_type.model}:{self.object_id}"
