"""
Example Django settings showing how to configure django-meme-maker.

Copy the relevant parts to your project's settings.py.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ... other Django settings ...

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Add meme_maker to your installed apps
    'meme_maker',
    
    # Your other apps...
    # 'your_app',
]

# Template configuration with optional context processor
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Optional: Add meme maker context processor to have
                # meme maker settings available in all templates
                'meme_maker.context_processors.meme_maker_context',
            ],
        },
    },
]

# Media files configuration (REQUIRED)
# Meme maker stores uploaded images in MEDIA_ROOT
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# =============================================================================
# MEME MAKER CONFIGURATION
# =============================================================================
# All settings are optional - defaults are shown below

MEME_MAKER = {
    # Path where meme images are uploaded (relative to MEDIA_ROOT)
    # Default: 'memes/'
    'UPLOAD_PATH': 'memes/',
    
    # Base template to extend. Set this to your site's base template
    # to have meme maker pages inherit your site's layout.
    # Default: 'meme_maker/base.html'
    'BASE_TEMPLATE': 'meme_maker/base.html',
    
    # For embedding in your site, you might use:
    # 'BASE_TEMPLATE': 'your_app/base.html',
    
    # Primary theme color (used in buttons, links, gradients)
    # Default: '#667eea'
    'PRIMARY_COLOR': '#667eea',
    
    # Secondary theme color (used in gradients)
    # Default: '#764ba2'
    'SECONDARY_COLOR': '#764ba2',
    
    # Title displayed in the meme maker header
    # Default: 'Meme Maker'
    'TITLE': 'Meme Maker',
    
    # Enable embed mode - renders without full page wrapper
    # Set to True when using your own base template
    # Default: False
    'EMBED_MODE': False,
    
    # Show navigation links (Create Meme, View All)
    # Default: True
    'SHOW_NAV': True,
    
    # Custom CSS to inject into meme maker pages
    # Default: ''
    'CUSTOM_CSS': '''
        /* Add your custom CSS here */
    ''',
    
    # Name of the content block in your base template
    # The meme maker will render its content in this block
    # Default: 'content'
    'CONTENT_BLOCK_NAME': 'content',
}


# =============================================================================
# EXAMPLE: Custom Storage Backend (e.g., AWS S3)
# =============================================================================
# The meme maker automatically uses Django's default storage.
# To use S3 or another cloud storage:

# For Django 4.2+
# STORAGES = {
#     "default": {
#         "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
#     },
#     "staticfiles": {
#         "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
# }

# AWS Settings (if using S3)
# AWS_ACCESS_KEY_ID = 'your-access-key'
# AWS_SECRET_ACCESS_KEY = 'your-secret-key'
# AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
# AWS_S3_REGION_NAME = 'us-east-1'
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
# AWS_DEFAULT_ACL = 'public-read'

