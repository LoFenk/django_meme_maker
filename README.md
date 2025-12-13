# Django Meme Maker

A reusable Django app for creating and managing memes with customizable, embeddable templates. Perfect for adding meme creation functionality to any Django project.

## Features

- 📸 **Easy meme creation** - Upload images and add top/bottom text
- 🎨 **Customizable themes** - Configure colors, styles, and layouts
- 📦 **Embeddable components** - Include meme functionality in any template
- 💾 **Storage agnostic** - Works with any Django storage backend (local, S3, GCS, etc.)
- 🔌 **Plug and play** - Simple installation with sensible defaults
- 📱 **Responsive design** - Works great on all screen sizes

## Installation

### Via pip (from PyPI)

```bash
pip install django-meme-maker
```

### Via pip (from source/GitHub)

```bash
pip install git+https://github.com/yourusername/django-meme-maker.git
```

### For development

```bash
git clone https://github.com/yourusername/django-meme-maker.git
cd django-meme-maker
pip install -e ".[dev]"
```

## Quick Start

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'meme_maker',
]
```

### 2. Configure Media Settings

Make sure you have media settings configured in your project:

```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 3. Include URLs

```python
# urls.py
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... other urls
    path('memes/', include('meme_maker.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Done!

Visit `/memes/` to start creating memes!

## Configuration

Configure the meme maker in your `settings.py` using the `MEME_MAKER` dictionary:

```python
# settings.py
MEME_MAKER = {
    # Path where meme images are uploaded (relative to MEDIA_ROOT)
    'UPLOAD_PATH': 'memes/',
    
    # Base template to extend (for embedding into your site's layout)
    'BASE_TEMPLATE': 'meme_maker/base.html',
    
    # Primary theme color
    'PRIMARY_COLOR': '#667eea',
    
    # Secondary theme color (for gradients)
    'SECONDARY_COLOR': '#764ba2',
    
    # Title displayed in the meme maker
    'TITLE': 'Meme Maker',
    
    # Enable embed mode (minimal wrapper, no full page layout)
    'EMBED_MODE': False,
    
    # Show navigation links between pages
    'SHOW_NAV': True,
    
    # Custom CSS to inject into templates
    'CUSTOM_CSS': '',
    
    # Name of the content block in your base template
    'CONTENT_BLOCK_NAME': 'content',
}
```

## Integration Options

### Option 1: Standalone Pages (Default)

The meme maker works out of the box with its own base template. Just include the URLs:

```python
urlpatterns = [
    path('memes/', include('meme_maker.urls')),
]
```

### Option 2: Embed in Your Site Layout

To make the meme maker inherit your site's base template:

```python
# settings.py
MEME_MAKER = {
    'BASE_TEMPLATE': 'your_app/base.html',  # Your site's base template
    'EMBED_MODE': True,  # Don't render the outer page wrapper
}
```

Your base template should have a content block:

```html
<!-- your_app/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}My Site{% endblock %}</title>
    {% block extra_head %}{% endblock %}
</head>
<body>
    <nav><!-- Your navigation --></nav>
    
    <main>
        {% block content %}{% endblock %}
        <!-- Or use: {% block meme_maker_content %}{% endblock %} -->
    </main>
    
    <footer><!-- Your footer --></footer>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Option 3: Include Components in Your Templates

You can include meme maker components directly in your own templates:

```html
{% load meme_maker_tags %}

<!-- Include the styles -->
{% meme_maker_css %}

<!-- Display a single meme -->
{% render_meme meme %}

<!-- Display a meme with info and actions -->
{% render_meme meme show_info=True show_actions=True %}

<!-- Display a grid of memes -->
{% render_meme_grid memes %}

<!-- Display a meme card -->
{% render_meme_card meme %}

<!-- Get recent memes -->
{% get_recent_memes 6 as recent_memes %}
{% for meme in recent_memes %}
    {% render_meme_card meme %}
{% endfor %}
```

### Option 4: Include Component Templates Directly

```html
<!-- Include the styles in your head -->
{% include "meme_maker/components/styles.html" %}

<!-- Include the meme form -->
{% include "meme_maker/components/meme_form.html" with form=form %}

<!-- Include a meme display -->
{% include "meme_maker/components/meme_display.html" with meme=meme show_info=True %}

<!-- Include a meme grid -->
{% include "meme_maker/components/meme_grid.html" with memes=memes %}
```

## Context Processor (Optional)

To have meme maker settings available in all templates:

```python
# settings.py
TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                # ... other processors
                'meme_maker.context_processors.meme_maker_context',
            ],
        },
    },
]
```

Then in templates:

```html
{{ meme_maker_primary_color }}
{{ meme_maker_title }}
```

## Custom Styling

### Using CSS Variables

The meme maker uses CSS custom properties that you can override:

```css
:root {
    --meme-primary: #your-color;
    --meme-secondary: #your-color;
    --meme-gradient: linear-gradient(135deg, var(--meme-primary) 0%, var(--meme-secondary) 100%);
    --meme-text-dark: #1a1a2e;
    --meme-text-light: #6b7280;
    --meme-bg-light: #f8fafc;
    --meme-bg-white: #ffffff;
    --meme-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
    --meme-shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.08);
    --meme-radius: 16px;
    --meme-radius-sm: 10px;
}
```

### Using the CUSTOM_CSS Setting

```python
MEME_MAKER = {
    'CUSTOM_CSS': '''
        .meme-btn {
            background: #ff6b6b !important;
        }
        .meme-card {
            border: 2px solid #ddd;
        }
    ''',
}
```

### Overriding Templates

Create your own templates in `your_app/templates/meme_maker/` to override the defaults:

```
your_app/
  templates/
    meme_maker/
      base.html      # Override the base template
      create.html    # Override the create page
      detail.html    # Override the detail page
      list.html      # Override the list page
```

## Storage Configuration

The meme maker automatically uses Django's default storage backend. To use custom storage (like S3):

```python
# settings.py

# For Django 4.2+
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# AWS settings
AWS_ACCESS_KEY_ID = 'your-key'
AWS_SECRET_ACCESS_KEY = 'your-secret'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
```

## API Reference

### Models

#### `Meme`

```python
from meme_maker import Meme

# Create a meme
meme = Meme.objects.create(
    image=uploaded_file,
    top_text='Hello',
    bottom_text='World'
)

# Access properties
meme.image.url  # URL of the image
meme.get_absolute_url()  # URL to the detail page
meme.created_at  # Creation timestamp
```

### Forms

#### `MemeForm`

```python
from meme_maker import MemeForm

form = MemeForm(request.POST, request.FILES)
if form.is_valid():
    meme = form.save()
```

#### `MemeEditForm`

```python
from meme_maker import MemeEditForm

form = MemeEditForm(request.POST, request.FILES, instance=meme)
```

### Settings

```python
from meme_maker import meme_maker_settings

# Access settings
meme_maker_settings.PRIMARY_COLOR
meme_maker_settings.UPLOAD_PATH
meme_maker_settings.get_context()  # Get all settings as a dict
```

### Template Tags

```html
{% load meme_maker_tags %}

{% meme_maker_css %}                           {# Include CSS styles #}
{% get_meme_maker_settings as settings %}      {# Get settings dict #}
{% render_meme meme %}                         {# Render a meme #}
{% render_meme_card meme %}                    {# Render a meme card #}
{% render_meme_grid memes %}                   {# Render a meme grid #}
{% get_recent_memes 6 as recent %}             {# Get recent memes #}
```

## URLs

| URL Pattern | Name | Description |
|-------------|------|-------------|
| `/` | `meme_maker:home` | Redirects to create page |
| `/create/` | `meme_maker:create` | Create a new meme |
| `/meme/<id>/` | `meme_maker:detail` | View a single meme |
| `/memes/` | `meme_maker:list` | List all memes |

## Class-Based Views

For more flexibility, use the class-based views:

```python
from meme_maker.views import MemeCreateView, MemeDetailView, MemeListView

urlpatterns = [
    path('create/', MemeCreateView.as_view(), name='create'),
    path('meme/<int:pk>/', MemeDetailView.as_view(), name='detail'),
    path('list/', MemeListView.as_view(), name='list'),
]
```

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Building the Package

```bash
pip install build twine
python -m build
twine upload dist/*
```

## Requirements

- Python 3.10+
- Django 4.2+
- Pillow 9.0+

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
