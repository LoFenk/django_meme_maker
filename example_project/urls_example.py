"""
Example URL configuration showing how to include django-meme-maker URLs.

Copy the relevant parts to your project's urls.py.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Include meme maker URLs
    # All meme maker views will be available under /memes/
    path('memes/', include('meme_maker.urls')),
    
    # You can also use a different prefix:
    # path('fun/create-meme/', include('meme_maker.urls')),
    
    # Or mount at root (not recommended if you have other views):
    # path('', include('meme_maker.urls')),
    
    # Your other URL patterns...
    # path('', include('your_app.urls')),
]

# Serve media files in development
# In production, configure your web server (nginx, Apache) to serve media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# =============================================================================
# ALTERNATIVE: Using Class-Based Views for Custom URLs
# =============================================================================
# If you want more control over the URL patterns, you can use the CBVs directly:

# from meme_maker.views import MemeCreateView, MemeDetailView, MemeListView

# urlpatterns = [
#     # Custom meme maker URLs
#     path('create-your-meme/', MemeCreateView.as_view(), name='custom_create'),
#     path('view-meme/<int:pk>/', MemeDetailView.as_view(), name='custom_detail'),
#     path('browse-memes/', MemeListView.as_view(), name='custom_list'),
# ]


# =============================================================================
# ALTERNATIVE: Custom Views with Your Own Logic
# =============================================================================
# You can also create your own views that use the meme maker models and forms:

# from django.shortcuts import render, redirect
# from meme_maker import Meme, MemeForm
#
# def my_custom_meme_view(request):
#     if request.method == 'POST':
#         form = MemeForm(request.POST, request.FILES)
#         if form.is_valid():
#             meme = form.save()
#             # Add your custom logic here
#             return redirect('meme_detail', pk=meme.pk)
#     else:
#         form = MemeForm()
#     
#     return render(request, 'my_template.html', {
#         'form': form,
#         'recent_memes': Meme.objects.all()[:5],
#     })

