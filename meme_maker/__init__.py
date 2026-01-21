"""
Django Meme Maker
=================

A reusable Django app for creating and managing memes with a searchable
template bank and customizable embeddable templates.

Features:
- Template Bank: Search and browse meme templates by title/tags
- Meme Editor: Create memes from templates with customizable text overlays
- Image Generation: Automatic composite image generation with Pillow
- Download Support: Download templates and generated memes
- Storage Agnostic: Works with any Django storage backend

Quick Start:
    1. Install: pip install django-meme-maker
    2. Add 'meme_maker' to INSTALLED_APPS
    3. Include meme_maker.urls in your URLconf
    4. Run migrations: python manage.py migrate

For configuration options, see the README or the conf module.

Usage after Django is loaded:
    from meme_maker import Meme, MemeTemplate, MemeForm, meme_maker_settings
"""

__version__ = '1.2.5'
__author__ = 'Paul Stoica'


def get_version():
    """Return the version string."""
    return __version__


# Lazy imports to avoid AppRegistryNotReady errors
# These are only imported when accessed, after Django is fully loaded

def __getattr__(name):
    """Lazy import of models and forms to avoid AppRegistryNotReady errors."""
    if name == 'Meme':
        from .models import Meme
        return Meme
    elif name == 'MemeTemplate':
        from .models import MemeTemplate
        return MemeTemplate
    elif name == 'MemeForm':
        from .forms import MemeForm
        return MemeForm
    elif name == 'MemeEditForm':
        from .forms import MemeEditForm
        return MemeEditForm
    elif name == 'MemeTemplateForm':
        from .forms import MemeTemplateForm
        return MemeTemplateForm
    elif name == 'MemeEditorForm':
        from .forms import MemeEditorForm
        return MemeEditorForm
    elif name == 'meme_maker_settings':
        from .conf import meme_maker_settings
        return meme_maker_settings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'Meme',
    'MemeTemplate',
    'MemeForm',
    'MemeEditForm',
    'MemeTemplateForm',
    'MemeEditorForm',
    'meme_maker_settings',
    '__version__',
    'get_version',
]
