# Preface
Let me first be honest here, this is a vibe coded project for my own use. All Credit to Claude Opus 4.5 on Cursor - incredible work. This very paragraph some of the little work I did - other than fiddling around with prompts. I have no merit otherwise. Feel free to reuse as you see fit.


# Django Meme Maker

A reusable Django app for creating and managing memes with a searchable template bank and customizable, embeddable templates. Perfect for adding meme creation functionality to any Django project.

## Features

- 🔍 **Template Bank** - Searchable library of meme templates by title and tags
- ✨ **Meme Editor** - Create memes from templates with customizable text overlays
- 🎨 **Text Styling** - Configure colors, font size, and positioning
- 📥 **Download Support** - Download both templates and generated memes
- 🖼️ **Image Generation** - Automatic composite image generation with Pillow
- 💧 **Watermark Support** - Add your logo/watermark to all generated memes
- ⭐ **Rating System** - Rate templates and memes with star ratings
- 🔗 **Object Linking** - Link memes/templates to any model (Users, Products, etc.)
- 💾 **Storage agnostic** - Works with any Django storage backend (local, S3, GCS, etc.)
- 📦 **Embeddable components** - Include meme functionality in any template
- 🔌 **Plug and play** - Simple installation with sensible defaults
- 📱 **Responsive design** - Works great on all screen sizes

## User Workflow

1. **Browse Templates** - Search the template bank by name or tags
2. **Select Template** - View template details and click "Make My Own"
3. **Edit Meme** - Add top/bottom text with custom styling
4. **Save & Share** - Download the generated meme or share via URL

If no template exists, users can **upload their own** and immediately create a meme from it.

## Installation

### Via pip (from PyPI)

```bash
pip install django-meme-maker
```

### Via pip (from source/GitHub)

```bash
pip install git+https://github.com/LoFenk/django_meme_maker.git
```

### For development

```bash
git clone https://github.com/LoFenk/django_meme_maker.git
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

Visit `/memes/` to start browsing templates and creating memes!

## Configuration

Configure the meme maker in your `settings.py` using the `MEME_MAKER` dictionary:

```python
# settings.py
MEME_MAKER = {
    # Path where meme images are uploaded (relative to MEDIA_ROOT)
    'UPLOAD_PATH': 'memes/',
    
    # Base template to extend (for embedding into your site's layout)
    # NOTE: Your base template MUST have {% block content %}{% endblock %}
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
    
    # Watermark image path (absolute path or relative to STATIC_ROOT/STATICFILES_DIRS)
    # If set, this image will be placed at the bottom-right corner of all generated memes
    'WATERMARK_IMAGE': None,  # e.g., '/path/to/watermark.png' or 'images/my-watermark.png'
    
    # Watermark opacity (0.0 to 1.0, where 1.0 is fully opaque)
    'WATERMARK_OPACITY': 0.7,
    
    # Watermark scale (relative to meme width, e.g., 0.15 = 15% of meme width)
    'WATERMARK_SCALE': 0.15,
    
    # Watermark padding from edges (in pixels)
    'WATERMARK_PADDING': 10,
}
```

### Watermark Configuration

To add your logo or watermark to all generated memes:

```python
# settings.py
MEME_MAKER = {
    # Option 1: Absolute path to watermark image
    'WATERMARK_IMAGE': '/absolute/path/to/watermark.png',
    
    # Option 2: Path relative to your static files
    'WATERMARK_IMAGE': 'images/my-watermark.png',
    
    # Customize appearance
    'WATERMARK_OPACITY': 0.7,   # 70% opaque
    'WATERMARK_SCALE': 0.15,    # 15% of meme width
    'WATERMARK_PADDING': 10,    # 10px from edges
}
```

The watermark will be automatically scaled to maintain aspect ratio and placed in the bottom-right corner of all generated meme images.

**Tip:** Use a transparent PNG for best results.

## URLs Reference

| URL Pattern | Name | Description |
|-------------|------|-------------|
| `/` | `meme_maker:home` | Redirects to template list |
| `/templates/` | `meme_maker:template_list` | Search and browse templates |
| `/templates/<pk>/` | `meme_maker:template_detail` | View template details |
| `/templates/upload/` | `meme_maker:template_upload` | Upload new template |
| `/templates/<pk>/download/` | `meme_maker:template_download` | Download template image |
| `/editor/<template_pk>/` | `meme_maker:meme_editor` | Create meme from template |
| `/meme/<pk>/` | `meme_maker:meme_detail` | View a meme |
| `/meme/<pk>/download/` | `meme_maker:meme_download` | Download meme image |
| `/memes/` | `meme_maker:meme_list` | List all memes |
| `/create/` | `meme_maker:create` | Legacy: direct meme creation |

## Data Models

### MemeTemplate

Stores reusable meme template images with searchable metadata.

```python
from meme_maker import MemeTemplate

# Create a template
template = MemeTemplate.objects.create(
    image=uploaded_file,
    title='Distracted Boyfriend',
    tags='funny, reaction, relationship'
)

# Search templates
results = MemeTemplate.search('funny')

# Get tags as list
tags = template.get_tags_list()  # ['funny', 'reaction', 'relationship']
```

### Meme

Stores user-created memes with text overlays and generated composite images.

```python
from meme_maker import Meme

# Create from template
meme = Meme(template=template)
meme.set_overlays([
    {
        'text': 'When you see a bug',
        'position': 'top',
        'color': '#FFFFFF',
        'stroke_color': '#000000',
    },
    {
        'text': 'In production',
        'position': 'bottom',
        'color': '#FFFFFF', 
        'stroke_color': '#000000',
    }
])
meme.save()  # Automatically generates composite image

# Get display URL (prefers generated image)
url = meme.get_display_image_url()
```

#### Text Overlay JSON Schema

```json
{
    "overlays": [
        {
            "text": "Hello World",
            "position": "top",
            "x": 50,
            "y": 10,
            "font_size": 48,
            "color": "#FFFFFF",
            "stroke_color": "#000000",
            "stroke_width": 2,
            "uppercase": true
        }
    ]
}
```

## Image Generation Strategy

The app uses a **hybrid approach** for optimal performance and flexibility:

1. **Text Overlays as JSON** - Stored in `Meme.text_overlays` for future editing
2. **Pre-generated Composite Image** - Stored in `Meme.generated_image` for fast downloads

When a meme is saved:
- Pillow renders the text onto the template image
- The composite is saved to storage
- Downloads serve the pre-rendered image (fast)
- If Pillow fails, CSS-based overlay is used as fallback

## Integration Options

### Option 1: Standalone Pages (Default)

The meme maker works out of the box with its own base template:

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
    'BASE_TEMPLATE': 'your_app/base.html',
    'EMBED_MODE': True,
}
```

**Your base template must have these blocks:**

```html
<!DOCTYPE html>
<html>
<head>
    <!-- Your head content -->
    {% block extra_head %}{% endblock %}  <!-- Required for meme_maker CSS -->
</head>
<body>
    {% block content %}{% endblock %}      <!-- Required for page content -->
    
    {% block extra_js %}{% endblock %}     <!-- Required for meme_maker JS -->
</body>
</html>
```

The `extra_head` and `extra_js` blocks allow meme_maker to inject its CSS and JavaScript when using your custom base template.

### Option 3: Include Components in Your Templates

```html
{% load meme_maker_tags %}

{% meme_maker_css %}

<!-- Get recent templates -->
{% get_recent_templates 6 as templates %}

<!-- Render meme components -->
{% render_meme meme %}
{% render_meme_card meme %}
{% render_meme_grid memes %}
```

## Forms Reference

### MemeTemplateForm

For uploading new templates:

```python
from meme_maker import MemeTemplateForm

form = MemeTemplateForm(request.POST, request.FILES)
if form.is_valid():
    template = form.save()
```

### MemeEditorForm

For creating memes with text overlays:

```python
from meme_maker import MemeEditorForm

form = MemeEditorForm(request.POST)
if form.is_valid():
    overlays = form.get_overlays()
    meme = Meme(template=template)
    meme.set_overlays(overlays)
    meme.save()
```

### MemeForm (Legacy)

For direct meme creation without templates:

```python
from meme_maker import MemeForm

form = MemeForm(request.POST, request.FILES)
if form.is_valid():
    meme = form.save()
```

## Class-Based Views

For more flexibility, use the class-based views:

```python
from meme_maker.views import (
    MemeTemplateListView,
    MemeTemplateDetailView,
    MemeTemplateCreateView,
    MemeCreateView,
    MemeDetailView,
    MemeListView,
)

urlpatterns = [
    path('templates/', MemeTemplateListView.as_view(), name='templates'),
    path('templates/<int:pk>/', MemeTemplateDetailView.as_view(), name='template_detail'),
    path('create/', MemeCreateView.as_view(), name='create'),
    path('meme/<int:pk>/', MemeDetailView.as_view(), name='detail'),
    path('list/', MemeListView.as_view(), name='list'),
]
```

## Search Behavior

Template search works on:
- **Title** (case-insensitive contains)
- **Tags** (case-insensitive contains)

Uses `icontains` for database-agnostic compatibility (SQLite, PostgreSQL, MySQL).

```python
# Search via model method
templates = MemeTemplate.search('funny cat')

# Search via view (GET parameter)
# /memes/templates/?q=funny+cat
```

## Storage Configuration

The meme maker automatically uses Django's default storage backend:

```python
# settings.py - For S3 storage
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

AWS_ACCESS_KEY_ID = 'your-key'
AWS_SECRET_ACCESS_KEY = 'your-secret'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
```

## Custom Styling

### Using CSS Variables

```css
:root {
    --meme-primary: #your-color;
    --meme-secondary: #your-color;
    --meme-gradient: linear-gradient(135deg, var(--meme-primary) 0%, var(--meme-secondary) 100%);
}
```

### Using CUSTOM_CSS Setting

```python
MEME_MAKER = {
    'CUSTOM_CSS': '''
        .meme-btn { background: #ff6b6b !important; }
        .meme-card { border: 2px solid #ddd; }
    ''',
}
```

## Content Security Policy (CSP)

All JavaScript and CSS are served from static files, making CSP configuration straightforward.

### Basic CSP Configuration

```python
# For django-csp or similar packages
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:")
```

### If Using django-csp

If you have [django-csp](https://github.com/mozilla/django-csp) installed with nonce support, meme_maker templates will automatically use the `CSP_NONCE` context variable:

```html
<!-- This is handled automatically in meme_maker templates -->
<script nonce="{{ CSP_NONCE }}" src="..."></script>
<style nonce="{{ CSP_NONCE }}">...</style>
```

No additional configuration needed—just ensure your django-csp middleware is set up.

### If Using Custom Colors (Inline Style)

When you configure `PRIMARY_COLOR`, `SECONDARY_COLOR`, or `CUSTOM_CSS`, a small inline `<style>` block is rendered. Options:

1. **Use django-csp** - Nonce is automatically applied
2. **Add style hash to CSP** - Calculate hash of the style content
3. **Use `'unsafe-inline'` for styles** - Less secure but simplest:
   ```python
   CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
   ```
4. **Skip custom colors** - Use defaults from static CSS file (no inline styles needed)

### If NOT Using django-csp

If you use a different CSP package or manual headers, and need nonces:

1. Ensure your middleware adds `CSP_NONCE` to the template context
2. Meme_maker templates check for `{% if CSP_NONCE %}` automatically

If your nonce variable has a different name, you'll need to either:
- Rename it to `CSP_NONCE` in your context processor
- Override meme_maker templates in your project

## Admin Interface

Both models are registered with the Django admin:

- **MemeTemplate Admin**: Preview, search by title/tags, view meme count, view linked objects
- **Meme Admin**: Preview, template info, regenerate images action, view linked objects
- **TemplateLink / MemeLink Admin**: Manage object links directly

## Object Linking

Link memes and templates to **any object** in your project (Users, Products, Campaigns, etc.) using Django's ContentTypes framework.

### Linking Objects

```python
from myapp.models import Product, Campaign
from meme_maker.models import Meme, MemeTemplate

# Link a meme to multiple objects
meme = Meme.objects.get(pk=1)
meme.link_to(product)
meme.link_to(user)
meme.link_to(campaign)

# Link with optional metadata
meme.link_to(product, link_type='featured')
meme.link_to(user, link_type='created_by', metadata={'source': 'api'})

# Same for templates
template = MemeTemplate.objects.get(pk=1)
template.link_to(brand)
template.link_to(category)
```

### Checking Links

```python
# Check if linked
meme.is_linked_to(product)  # True/False

# Get all linked objects
meme.get_linked_objects()  # [<Product>, <User>, <Campaign>]

# Get linked objects of a specific type
meme.get_linked_objects(Product)  # [<Product>]

# Get link instances (to access link_type and metadata)
links = meme.get_links()
for link in links:
    print(f"{link.linked_object} - {link.link_type}")
```

### Unlinking

```python
meme.unlink_from(product)  # Returns True if removed, False if didn't exist
```

### Querying by Linked Object

```python
# Get all memes linked to a product
memes = Meme.objects.linked_to(product)

# Get all templates linked to a campaign
templates = MemeTemplate.objects.linked_to(campaign)

# Combine with other filters
recent_memes = Meme.objects.linked_to(user).filter(created_at__gte=last_week)
```

### Use Cases

- **User ownership**: `meme.link_to(request.user, link_type='created_by')`
- **Product association**: `meme.link_to(product, link_type='promotional')`
- **Campaign tracking**: `template.link_to(campaign, link_type='source')`
- **Content curation**: `template.link_to(collection, link_type='featured')`

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

## Backward Compatibility

Existing memes created before the template bank update will continue to work:
- Direct image uploads are still supported
- Legacy `top_text` and `bottom_text` fields are preserved
- Old URL patterns (`/create/`, `/detail/<pk>/`) still work

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
