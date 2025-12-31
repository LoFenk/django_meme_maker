"""
Template tags for django-meme-maker.

Usage in templates:
    {% load meme_maker_tags %}
    
    {# Get all meme maker settings #}
    {% meme_maker_settings as settings %}
    {{ settings.primary_color }}
    
    {# Include the meme maker styles #}
    {% meme_maker_css %}
    
    {# Render a meme with text overlay #}
    {% render_meme meme %}
    
    {# Render a meme card #}
    {% render_meme_card meme %}
    
    {# Render a grid of memes #}
    {% render_meme_grid memes %}
"""

from django import template
from django.utils.safestring import mark_safe

from ..conf import meme_maker_settings
from ..models import Meme

register = template.Library()


@register.simple_tag
def meme_maker_css():
    """
    Output the meme maker CSS styles.
    
    Usage:
        {% load meme_maker_tags %}
        {% meme_maker_css %}
    """
    primary = meme_maker_settings.PRIMARY_COLOR
    secondary = meme_maker_settings.SECONDARY_COLOR
    custom_css = meme_maker_settings.CUSTOM_CSS
    
    css = f'''
    <style>
        :root {{
            --meme-primary: {primary};
            --meme-secondary: {secondary};
            --meme-gradient: linear-gradient(135deg, var(--meme-primary) 0%, var(--meme-secondary) 100%);
            --meme-text-dark: #1a1a2e;
            --meme-text-light: #6b7280;
            --meme-bg-light: #f8fafc;
            --meme-bg-white: #ffffff;
            --meme-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
            --meme-shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.08);
            --meme-radius: 16px;
            --meme-radius-sm: 10px;
        }}
        
        .meme-display {{ position: relative; display: inline-block; margin: 0 auto; text-align: center; width: 100%; }}
        .meme-display-wrapper {{ position: relative; display: inline-block; max-width: 100%; }}
        .meme-image {{ max-width: 100%; height: auto; border-radius: var(--meme-radius-sm); box-shadow: var(--meme-shadow-sm); }}
        .meme-text-overlay {{ position: absolute; left: 50%; transform: translateX(-50%); color: white; font-weight: 900; font-size: clamp(1.25rem, 4vw, 2.5rem); text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000; text-transform: uppercase; letter-spacing: 0.05em; max-width: 90%; word-wrap: break-word; text-align: center; line-height: 1.2; }}
        .meme-text-top {{ top: 1rem; }}
        .meme-text-bottom {{ bottom: 1rem; }}
        .meme-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; }}
        .meme-card {{ background: var(--meme-bg-light); border-radius: var(--meme-radius-sm); overflow: hidden; box-shadow: var(--meme-shadow-sm); transition: transform 0.2s ease, box-shadow 0.2s ease; text-decoration: none; color: inherit; display: block; }}
        .meme-card:hover {{ transform: translateY(-4px); box-shadow: var(--meme-shadow); }}
        .meme-card-image {{ width: 100%; height: 220px; object-fit: cover; }}
        .meme-card-body {{ padding: 1rem 1.25rem; }}
        .meme-card-title {{ color: var(--meme-text-dark); font-weight: 600; margin: 0 0 0.5rem 0; font-size: 1rem; }}
        .meme-card-text {{ color: var(--meme-text-light); font-size: 0.875rem; margin: 0.25rem 0; }}
        .meme-card-meta {{ font-size: 0.75rem; color: #9ca3af; margin-top: 0.75rem; }}
        .meme-btn {{ display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; background: var(--meme-gradient); color: white; padding: 0.875rem 2rem; border: none; border-radius: var(--meme-radius-sm); font-size: 1rem; font-weight: 600; cursor: pointer; text-decoration: none; }}
        .meme-btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.35); }}
        {custom_css}
    </style>
    '''
    return mark_safe(css)


@register.simple_tag
def get_meme_maker_settings():
    """
    Get all meme maker settings as a dict.
    
    Usage:
        {% get_meme_maker_settings as mm_settings %}
        {{ mm_settings.PRIMARY_COLOR }}
    """
    return {
        'PRIMARY_COLOR': meme_maker_settings.PRIMARY_COLOR,
        'SECONDARY_COLOR': meme_maker_settings.SECONDARY_COLOR,
        'TITLE': meme_maker_settings.TITLE,
        'EMBED_MODE': meme_maker_settings.EMBED_MODE,
        'SHOW_NAV': meme_maker_settings.SHOW_NAV,
        'BASE_TEMPLATE': meme_maker_settings.BASE_TEMPLATE,
        'UPLOAD_PATH': meme_maker_settings.UPLOAD_PATH,
        'CUSTOM_CSS': meme_maker_settings.CUSTOM_CSS,
    }


@register.inclusion_tag('meme_maker/components/meme_display.html')
def render_meme(meme, show_info=False, show_actions=False):
    """
    Render a meme with text overlay.
    
    Usage:
        {% render_meme meme %}
        {% render_meme meme show_info=True %}
        {% render_meme meme show_actions=True %}
    """
    return {
        'meme': meme,
        'show_info': show_info,
        'show_actions': show_actions,
    }


@register.inclusion_tag('meme_maker/components/meme_card.html')
def render_meme_card(meme, show_link=True, show_text=True, show_date=True):
    """
    Render a meme as a card.
    
    Usage:
        {% render_meme_card meme %}
        {% render_meme_card meme show_link=False %}
    """
    return {
        'meme': meme,
        'show_link': show_link,
        'show_text': show_text,
        'show_date': show_date,
    }


@register.inclusion_tag('meme_maker/components/meme_grid.html')
def render_meme_grid(memes, show_empty=True, max_items=None):
    """
    Render a grid of meme cards.
    
    Usage:
        {% render_meme_grid memes %}
        {% render_meme_grid memes max_items=6 %}
    """
    return {
        'memes': memes,
        'show_empty': show_empty,
        'max_items': max_items or 999,
    }


@register.simple_tag
def get_recent_memes(count=6):
    """
    Get the most recent memes.
    
    Usage:
        {% get_recent_memes 6 as recent_memes %}
        {% for meme in recent_memes %}...{% endfor %}
    """
    return Meme.objects.all()[:count]

