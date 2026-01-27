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
    
    # Watermark image path (absolute path or relative to STATIC_ROOT/STATICFILES_DIRS)
    # If set, this image will be placed at the bottom-right corner of all generated memes
    # Example: '/path/to/watermark.png' or 'images/my-watermark.png'
    'WATERMARK_IMAGE': None,
    
    # Watermark opacity (0.0 to 1.0, where 1.0 is fully opaque)
    'WATERMARK_OPACITY': 0.7,
    
    # Watermark scale (relative to meme width, e.g., 0.15 = 15% of meme width)
    'WATERMARK_SCALE': 0.15,
    
    # Watermark padding from edges (in pixels)
    'WATERMARK_PADDING': 10,

    # Optional linked object resolver for scoping templates/memes
    # Accepts a dotted path or callable that receives request
    # and returns a model instance or None
    'LINKED_OBJECT_RESOLVER': None,

    # Optional template set name for themed frontends
    # If set, templates are loaded from meme_maker/<TEMPLATE_SET>/... with fallback
    'TEMPLATE_SET': None,

    # Imgflip search integration (optional)
    'IMGFLIP_USERNAME': None,
    'IMGFLIP_PASSWORD': None,
    'IMGFLIP_DEFAULT_TYPE': 'image',
    'IMGFLIP_INCLUDE_NSFW': False,
    'IMGFLIP_CACHE_DAYS': 30,
    'ENABLE_IMGFLIP_SEARCH': False,
    
    # Custom font path for meme text rendering
    # If not set, uses system Impact font or bundled Anton font
    # Example: '/path/to/custom-font.ttf'
    'FONT_PATH': None,
}
"""

from django.conf import settings


class MemeMakerSettings:
    """
    A settings object that allows meme maker settings to be accessed as properties.
    
    Example:
        from meme_maker.conf import meme_maker_settings
        print(meme_maker_settings.UPLOAD_PATH)
        print(meme_maker_settings.WATERMARK_IMAGE)
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
        # Watermark settings
        'WATERMARK_IMAGE': None,  # Path to watermark image
        'WATERMARK_OPACITY': 0.7,  # 0.0 to 1.0
        'WATERMARK_SCALE': 0.15,  # Relative to meme width
        'WATERMARK_PADDING': 10,  # Pixels from edge
        'LINKED_OBJECT_RESOLVER': None,  # Callable or dotted path
        'TEMPLATE_SET': None,  # Template theme folder name
        # Imgflip search integration (optional)
        'IMGFLIP_USERNAME': None,
        'IMGFLIP_PASSWORD': None,
        'IMGFLIP_DEFAULT_TYPE': 'image',
        'IMGFLIP_INCLUDE_NSFW': False,
        'IMGFLIP_CACHE_DAYS': 30,
        'ENABLE_IMGFLIP_SEARCH': False,
        'FONT_PATH': None,  # Custom font path for meme text
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
        template_set = getattr(self, 'TEMPLATE_SET', None)
        base_template = getattr(self, 'BASE_TEMPLATE', None)
        default_base = self.DEFAULTS.get('BASE_TEMPLATE', 'meme_maker/base.html')
        if template_set and (not base_template or base_template == default_base):
            base_template = f"meme_maker/{template_set}/base.html"
        context['meme_maker_base_template'] = base_template
        context['meme_maker_template_base'] = (
            f"meme_maker/{template_set}" if template_set else "meme_maker"
        )
        context['meme_maker_uses_builtin_base'] = (
            bool(base_template) and base_template.startswith("meme_maker/")
        )
        if template_set in ('compact', 'modern', 'tech', 'classic'):
            context['meme_maker_theme_css'] = f"meme_maker/css/theme_{template_set}.css"
        else:
            context['meme_maker_theme_css'] = None
        return context


# Global settings instance
meme_maker_settings = MemeMakerSettings()
