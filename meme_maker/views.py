"""
Views for django-meme-maker.

Provides views for:
- Template bank (search, list, detail, upload)
- Meme editor (create memes from templates)
- Meme display and download
- Legacy views for backward compatibility
"""

import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404
from django.contrib import messages
from django.views.generic import CreateView, DetailView, ListView
from django.core.files.storage import default_storage

from .models import Meme, MemeTemplate
from .forms import (
    MemeForm, MemeEditForm, MemeTemplateForm, 
    MemeTemplateSearchForm, MemeEditorForm
)
from .conf import meme_maker_settings


def get_meme_maker_context():
    """Get the meme maker configuration context for templates."""
    return meme_maker_settings.get_context()


# =============================================================================
# HOME / NAVIGATION
# =============================================================================

def home(request):
    """
    Home page view - now redirects to template search.
    This is the new default entry point for the meme maker.
    """
    return redirect('meme_maker:template_list')


# =============================================================================
# TEMPLATE BANK VIEWS
# =============================================================================

def template_list(request):
    """
    Template search and list page.
    
    Users can search templates by title and tags.
    Shows a grid of available templates.
    """
    form = MemeTemplateSearchForm(request.GET)
    query = request.GET.get('q', '').strip()
    
    if query:
        templates = MemeTemplate.search(query)
    else:
        templates = MemeTemplate.objects.all()
    
    context = {
        'templates': templates,
        'search_form': form,
        'query': query,
        'title': 'Template Bank',
        'page_type': 'template_list',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/template_list.html', context)


def template_detail(request, pk):
    """
    Template detail page.
    
    Shows the template image and provides:
    - Download template button
    - "Make my own" button → links to meme editor
    """
    template = get_object_or_404(MemeTemplate, pk=pk)
    
    # Get recent memes made from this template
    recent_memes = template.memes.all()[:6]
    
    context = {
        'template': template,
        'recent_memes': recent_memes,
        'title': template.title,
        'page_type': 'template_detail',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/template_detail.html', context)


def template_upload(request):
    """
    Upload a new meme template.
    
    After successful upload, redirects to the meme editor
    to create a meme from the new template.
    """
    if request.method == 'POST':
        form = MemeTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Template "{template.title}" uploaded successfully!')
            # Redirect to editor to create a meme from this template
            return redirect('meme_maker:meme_editor', template_pk=template.pk)
    else:
        form = MemeTemplateForm()
    
    context = {
        'form': form,
        'title': 'Upload Template',
        'page_type': 'template_upload',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/template_upload.html', context)


def template_download(request, pk):
    """
    Download a template image.
    
    Returns the template image file as a download.
    """
    template = get_object_or_404(MemeTemplate, pk=pk)
    
    if not template.image:
        raise Http404("Template has no image")
    
    # Get file from storage
    try:
        file_handle = default_storage.open(template.image.name, 'rb')
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(template.image.name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Create response
        response = FileResponse(
            file_handle,
            content_type=content_type,
        )
        
        # Set download filename
        filename = template.image.name.split('/')[-1]
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception:
        raise Http404("Could not retrieve template image")


# =============================================================================
# MEME EDITOR VIEWS
# =============================================================================

def meme_editor(request, template_pk):
    """
    Meme editor page.
    
    Allows users to add text overlays to a template and save as a new meme.
    """
    template = get_object_or_404(MemeTemplate, pk=template_pk)
    
    if request.method == 'POST':
        form = MemeEditorForm(request.POST)
        if form.is_valid():
            # Create new meme from template
            meme = Meme(template=template)
            
            # Get overlays from form
            overlays = form.get_overlays()
            meme.set_overlays(overlays)
            
            # Also set legacy fields for backward compatibility
            for overlay in overlays:
                if overlay.get('position') == 'top' and not meme.top_text:
                    meme.top_text = overlay.get('text', '')
                elif overlay.get('position') == 'bottom' and not meme.bottom_text:
                    meme.bottom_text = overlay.get('text', '')
            
            meme.save()
            messages.success(request, 'Meme created successfully!')
            return redirect('meme_maker:meme_detail', pk=meme.pk)
    else:
        form = MemeEditorForm()
    
    context = {
        'template': template,
        'form': form,
        'title': f'Create Meme - {template.title}',
        'page_type': 'meme_editor',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/meme_editor.html', context)


# =============================================================================
# MEME VIEWS
# =============================================================================

def meme_detail(request, pk):
    """
    View to display a single meme.
    
    Shows the meme with text overlays and provides download option.
    """
    meme = get_object_or_404(Meme, pk=pk)
    
    context = {
        'meme': meme,
        'title': f'Meme #{meme.pk}',
        'page_type': 'meme_detail',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/meme_detail.html', context)


def meme_list(request):
    """View to display all memes."""
    memes = Meme.objects.all()
    
    context = {
        'memes': memes,
        'title': 'All Memes',
        'page_type': 'meme_list',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/meme_list.html', context)


def meme_download(request, pk):
    """
    Download a meme image.
    
    Returns the generated composite image if available,
    otherwise returns the source image.
    """
    meme = get_object_or_404(Meme, pk=pk)
    
    # Prefer generated image, fall back to source
    image_field = meme.generated_image if meme.generated_image else meme.get_source_image()
    
    if not image_field:
        raise Http404("Meme has no image")
    
    try:
        file_handle = default_storage.open(image_field.name, 'rb')
        
        content_type, _ = mimetypes.guess_type(image_field.name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        response = FileResponse(
            file_handle,
            content_type=content_type,
        )
        
        filename = f"meme_{meme.pk}.{image_field.name.split('.')[-1]}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception:
        raise Http404("Could not retrieve meme image")


# =============================================================================
# LEGACY VIEWS (Backward Compatibility)
# =============================================================================

def create_meme(request):
    """
    Legacy view to create a meme with direct image upload.
    
    Kept for backward compatibility. New users should use the
    template bank workflow instead.
    """
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save()
            messages.success(request, 'Meme created successfully!')
            return redirect('meme_maker:meme_detail', pk=meme.pk)
    else:
        form = MemeForm()
    
    context = {
        'form': form,
        'title': 'Create Meme',
        'page_type': 'create',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/create.html', context)


# Alias for backward compatibility
def detail(request, pk):
    """Alias for meme_detail (backward compatibility)."""
    return meme_detail(request, pk)


# =============================================================================
# CLASS-BASED VIEWS
# =============================================================================

class MemeTemplateListView(ListView):
    """Class-based view for template list with search."""
    model = MemeTemplate
    template_name = 'meme_maker/template_list.html'
    context_object_name = 'templates'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if query:
            return MemeTemplate.search(query)
        return MemeTemplate.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = MemeTemplateSearchForm(self.request.GET)
        context['query'] = self.request.GET.get('q', '')
        context['title'] = 'Template Bank'
        context['page_type'] = 'template_list'
        context.update(get_meme_maker_context())
        return context


class MemeTemplateDetailView(DetailView):
    """Class-based view for template detail."""
    model = MemeTemplate
    template_name = 'meme_maker/template_detail.html'
    context_object_name = 'template'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_memes'] = self.object.memes.all()[:6]
        context['title'] = self.object.title
        context['page_type'] = 'template_detail'
        context.update(get_meme_maker_context())
        return context


class MemeTemplateCreateView(CreateView):
    """Class-based view for template upload."""
    model = MemeTemplate
    form_class = MemeTemplateForm
    template_name = 'meme_maker/template_upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Upload Template'
        context['page_type'] = 'template_upload'
        context.update(get_meme_maker_context())
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Template "{self.object.title}" uploaded successfully!')
        return response
    
    def get_success_url(self):
        return reverse('meme_maker:meme_editor', kwargs={'template_pk': self.object.pk})


class MemeCreateView(CreateView):
    """Legacy class-based view for creating memes."""
    model = Meme
    form_class = MemeForm
    template_name = 'meme_maker/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Meme'
        context['page_type'] = 'create'
        context.update(get_meme_maker_context())
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Meme created successfully!')
        return super().form_valid(form)


class MemeDetailView(DetailView):
    """Class-based view for viewing a single meme."""
    model = Meme
    template_name = 'meme_maker/meme_detail.html'
    context_object_name = 'meme'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Meme #{self.object.pk}'
        context['page_type'] = 'meme_detail'
        context.update(get_meme_maker_context())
        return context


class MemeListView(ListView):
    """Class-based view for listing all memes."""
    model = Meme
    template_name = 'meme_maker/meme_list.html'
    context_object_name = 'memes'
    paginate_by = 12
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'All Memes'
        context['page_type'] = 'meme_list'
        context.update(get_meme_maker_context())
        return context


# Need to import reverse for CBV success_url
from django.urls import reverse
