from django.apps import AppConfig
from django.conf import settings


class MemeMakerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meme_maker'
    verbose_name = 'Meme Maker'
    
    # Default settings for the meme maker app
    # These can be overridden in the project's settings.py
    
    @classmethod
    def get_setting(cls, name, default=None):
        """Get a setting from MEME_MAKER settings dict or return default."""
        meme_maker_settings = getattr(settings, 'MEME_MAKER', {})
        return meme_maker_settings.get(name, default)
    
    @classmethod
    def get_upload_path(cls):
        """Get the upload path for meme images."""
        return cls.get_setting('UPLOAD_PATH', 'memes/')
    
    @classmethod
    def get_base_template(cls):
        """Get the base template to extend from."""
        return cls.get_setting('BASE_TEMPLATE', 'meme_maker/base.html')
    
    @classmethod
    def get_primary_color(cls):
        """Get the primary color for the meme maker UI."""
        return cls.get_setting('PRIMARY_COLOR', '#667eea')
    
    @classmethod
    def get_secondary_color(cls):
        """Get the secondary color for the meme maker UI."""
        return cls.get_setting('SECONDARY_COLOR', '#764ba2')
    
    @classmethod
    def get_title(cls):
        """Get the title for the meme maker."""
        return cls.get_setting('TITLE', 'Meme Maker')
    
    @classmethod
    def get_embed_mode(cls):
        """Check if embed mode is enabled (renders without full page wrapper)."""
        return cls.get_setting('EMBED_MODE', False)
    
    @classmethod
    def get_show_nav(cls):
        """Check if navigation should be shown."""
        return cls.get_setting('SHOW_NAV', True)
    
    @classmethod
    def get_custom_css(cls):
        """Get custom CSS to inject into templates."""
        return cls.get_setting('CUSTOM_CSS', '')
    
    @classmethod
    def get_all_settings(cls):
        """Get all meme maker settings as a dict for template context."""
        return {
            'upload_path': cls.get_upload_path(),
            'base_template': cls.get_base_template(),
            'primary_color': cls.get_primary_color(),
            'secondary_color': cls.get_secondary_color(),
            'title': cls.get_title(),
            'embed_mode': cls.get_embed_mode(),
            'show_nav': cls.get_show_nav(),
            'custom_css': cls.get_custom_css(),
        }
