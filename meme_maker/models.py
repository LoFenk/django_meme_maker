from django.db import models
from django.urls import reverse
from django.core.files.storage import default_storage

from .conf import meme_maker_settings


def meme_upload_path(instance, filename):
    """
    Generate upload path for meme images.
    Uses the configured UPLOAD_PATH setting.
    Files are stored in MEDIA_ROOT/UPLOAD_PATH/
    """
    upload_path = meme_maker_settings.UPLOAD_PATH
    # Ensure path ends with /
    if not upload_path.endswith('/'):
        upload_path += '/'
    return f'{upload_path}{filename}'


class Meme(models.Model):
    """
    Model to store meme information.
    
    Uses Django's default storage backend, which means it will
    automatically use whatever storage is configured in the project
    (local filesystem, S3, GCS, etc.)
    """
    image = models.ImageField(
        upload_to=meme_upload_path,
        storage=default_storage,
        help_text="Image file for the meme"
    )
    top_text = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Text to display at the top of the meme"
    )
    bottom_text = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Text to display at the bottom of the meme"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Meme'
        verbose_name_plural = 'Memes'
    
    def __str__(self):
        text_preview = self.top_text or self.bottom_text or 'No text'
        return f"Meme {self.id} - {text_preview[:30]}..."
    
    def get_absolute_url(self):
        return reverse('meme_maker:detail', kwargs={'pk': self.pk})
    
    def get_image_url(self):
        """Get the URL for the meme image."""
        if self.image:
            return self.image.url
        return None
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove the image file from storage."""
        # Store image path before deletion
        image_path = self.image.name if self.image else None
        
        # Delete the model instance
        super().delete(*args, **kwargs)
        
        # Delete the image file from storage
        if image_path:
            try:
                default_storage.delete(image_path)
            except Exception:
                # Log or handle the error if needed
                pass
