"""
Django Meme Maker
=================

A reusable Django app for creating and managing memes with customizable 
embeddable templates.

Quick Start:
    1. Install: pip install django-meme-maker
    2. Add 'meme_maker' to INSTALLED_APPS
    3. Include meme_maker.urls in your URLconf
    4. Run migrations: python manage.py migrate

For configuration options, see the README or the conf module.

Usage after Django is loaded:
    from meme_maker import Meme, MemeForm, MemeEditForm, meme_maker_settings
"""

__version__ = '1.0.0'
__author__ = 'Your Name'


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
    elif name == 'MemeForm':
        from .forms import MemeForm
        return MemeForm
    elif name == 'MemeEditForm':
        from .forms import MemeEditForm
        return MemeEditForm
    elif name == 'meme_maker_settings':
        from .conf import meme_maker_settings
        return meme_maker_settings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'Meme',
    'MemeForm',
    'MemeEditForm',
    'meme_maker_settings',
    '__version__',
    'get_version',
]
