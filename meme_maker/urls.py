"""
URL configuration for django-meme-maker.

URL Structure:
    /                           → Home (redirects to template list)
    /templates/                 → Template search/list (supports ?order=rating)
    /templates/<pk>/            → Template detail
    /templates/upload/          → Upload new template
    /templates/<pk>/download/   → Download template image
    /templates/<pk>/rate/       → Rate a template (POST)
    /editor/<template_pk>/      → Meme editor for a template
    /meme/<pk>/                 → View a meme
    /meme/<pk>/download/        → Download meme image
    /meme/<pk>/rate/            → Rate a meme (POST)
    /memes/                     → List all memes (supports ?order=rating)
    /create/                    → Legacy: direct meme creation
"""

from django.urls import path
from . import views

app_name = 'meme_maker'

urlpatterns = [
    # Home - now redirects to template bank
    path('', views.home, name='home'),
    
    # Template Bank
    path('templates/', views.template_list, name='template_list'),
    path('templates/upload/', views.template_upload, name='template_upload'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/download/', views.template_download, name='template_download'),
    path('templates/<int:pk>/rate/', views.rate_template, name='rate_template'),
    
    # Meme Editor
    path('editor/<int:template_pk>/', views.meme_editor, name='meme_editor'),
    
    # Meme Views
    path('meme/<int:pk>/', views.meme_detail, name='meme_detail'),
    path('meme/<int:pk>/download/', views.meme_download, name='meme_download'),
    path('meme/<int:pk>/rate/', views.rate_meme, name='rate_meme'),
    path('memes/', views.meme_list, name='meme_list'),
    
    # Legacy URLs (backward compatibility)
    path('create/', views.create_meme, name='create'),
    path('detail/<int:pk>/', views.detail, name='detail'),  # Old detail URL
]
