"""
Context processors for django-meme-maker.

Add 'meme_maker.context_processors.meme_maker_settings' to your
TEMPLATES context_processors to make meme maker settings available
in all templates.
"""

from .conf import meme_maker_settings


def meme_maker_context(request):
    """
    Add meme maker settings to template context.
    
    Usage in settings.py:
        TEMPLATES = [
            {
                ...
                'OPTIONS': {
                    'context_processors': [
                        ...
                        'meme_maker.context_processors.meme_maker_context',
                    ],
                },
            },
        ]
    
    Then in templates:
        {{ meme_maker_primary_color }}
        {{ meme_maker_title }}
    """
    return meme_maker_settings.get_context()

