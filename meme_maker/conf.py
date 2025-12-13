"""
Configuration module for django-meme-maker.

This module provides easy access to meme maker settings.
Settings can be configured in your Django project's settings.py:

MEME_MAKER = {
    # Path where meme images will be uploaded (relative to MEDIA_ROOT)
    'UPLOAD_PATH': 'memes/',
    
    # Base template to extend (for embedding into your site's layout)
    'BASE_TEMPLATE': 'meme_maker/base.html',
    
    # Primary theme color
    'PRIMARY_COLOR': '#667eea',
    
    # Secondary theme color  
    'SECONDARY_COLOR': '#764ba2',
    
    # Title displayed in the meme maker
    'TITLE': 'Meme Maker',
    
    # Enable embed mode (minimal wrapper for embedding)
    'EMBED_MODE': False,
    
    # Show navigation links
    'SHOW_NAV': True,
    
    # Custom CSS to inject
    'CUSTOM_CSS': '',
}
"""

from django.conf import settings


class MemeMakerSettings:
    """
    A settings object that allows meme maker settings to be accessed as properties.
    
    Example:
        from meme_maker.conf import meme_maker_settings
        print(meme_maker_settings.UPLOAD_PATH)
    """
    
    DEFAULTS = {
        'UPLOAD_PATH': 'memes/',
        'BASE_TEMPLATE': 'meme_maker/base.html',
        'PRIMARY_COLOR': '#667eea',
        'SECONDARY_COLOR': '#764ba2',
        'TITLE': 'Meme Maker',
        'EMBED_MODE': False,
        'SHOW_NAV': True,
        'CUSTOM_CSS': '',
        'CONTENT_BLOCK_NAME': 'content',
    }
    
    def __init__(self):
        self._cached_settings = None
    
    @property
    def user_settings(self):
        if self._cached_settings is None:
            self._cached_settings = getattr(settings, 'MEME_MAKER', {})
        return self._cached_settings
    
    def __getattr__(self, attr):
        if attr not in self.DEFAULTS:
            raise AttributeError(f"Invalid meme maker setting: '{attr}'")
        
        return self.user_settings.get(attr, self.DEFAULTS[attr])
    
    def get_context(self):
        """Get all settings as a context dict for templates."""
        context = {}
        for key in self.DEFAULTS:
            context[f'meme_maker_{key.lower()}'] = getattr(self, key)
        return context


# Global settings instance
meme_maker_settings = MemeMakerSettings()

