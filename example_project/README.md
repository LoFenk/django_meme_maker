# Example Project

This folder contains example configuration files showing how to integrate `django-meme-maker` into an existing Django project.

## Files

- `settings_example.py` - Example Django settings showing meme maker configuration
- `urls_example.py` - Example URL configuration
- `base_template_example.html` - Example base template for embedding meme maker
- `integration_example.html` - Example of embedding meme components in a custom page

## Quick Integration Steps

1. Install the package:
   ```bash
   pip install django-meme-maker
   ```

2. Add to `INSTALLED_APPS`:
   ```python
   INSTALLED_APPS = [
       # ...
       'meme_maker',
   ]
   ```

3. Add to your `urls.py`:
   ```python
   path('memes/', include('meme_maker.urls')),
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. (Optional) Configure settings in `MEME_MAKER` dict

## Embedding in Your Site

To have the meme maker use your site's layout:

```python
MEME_MAKER = {
    'BASE_TEMPLATE': 'your_app/base.html',
    'EMBED_MODE': True,
}
```

Your base template should include blocks that meme maker can use:
- `{% block title %}` - Page title
- `{% block content %}` or `{% block content %}` - Main content
- `{% block extra_head %}` - Additional CSS/JS in head
- `{% block extra_js %}` - Additional JS at end of body

