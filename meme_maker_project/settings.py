"""
Django settings for meme_maker_project project.

This is a development/demo project to test the django-meme-maker app.
When distributing the package, this project is NOT included.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-z%13)rm8d&ip)gk3u+41wn4k7iy#l%^4s*4=(01a4uxg+=33fh'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # The meme maker app
    'meme_maker',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meme_maker_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Optional: Add meme maker context processor
                'meme_maker.context_processors.meme_maker_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'meme_maker_project.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Media files (user uploads)
# The meme maker uses these settings for storing uploaded images
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# MEME MAKER CONFIGURATION
# =============================================================================
# These are optional - the defaults work fine for most cases

MEME_MAKER = {
    # Where to store meme images (relative to MEDIA_ROOT)
    'UPLOAD_PATH': 'memes/',
    
    # Theme colors
    'PRIMARY_COLOR': '#667eea',
    'SECONDARY_COLOR': '#764ba2',
    
    # App title
    'TITLE': 'Meme Maker',
    
    # Show navigation between pages
    'SHOW_NAV': True,
    
    # Use the built-in base template (change to your own for embedding)
    'BASE_TEMPLATE': 'meme_maker/base.html',
    
    # Set to True when embedding in your site's layout
    'EMBED_MODE': False,
    
    # Custom CSS (empty by default)
    'CUSTOM_CSS': '',
}
