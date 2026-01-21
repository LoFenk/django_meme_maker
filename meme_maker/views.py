"""
Views for django-meme-maker.

Provides views for:
- Template bank (search, list, detail, upload)
- Meme editor (create memes from templates)
- Meme display and download
- Rating system for templates and memes
- Legacy views for backward compatibility
"""

import json
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404, JsonResponse
from django.contrib import messages
from django.views.generic import CreateView, DetailView, ListView
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .models import Meme, MemeTemplate, TemplateRating, MemeRating
from .forms import (
    MemeForm, MemeEditForm, MemeTemplateForm, 
    MemeTemplateSearchForm, MemeEditorForm
)
from .conf import meme_maker_settings


def get_meme_maker_context():
    """Get the meme maker configuration context for templates."""
    return meme_maker_settings.get_context()

def resolve_linked_object(request):
    """Resolve a linked object for scoping templates/memes, if configured."""
    resolver = meme_maker_settings.LINKED_OBJECT_RESOLVER
    if not resolver:
        return None
    if isinstance(resolver, str):
        resolver = import_string(resolver)
    if not callable(resolver):
        raise ImproperlyConfigured(
            "MEME_MAKER['LINKED_OBJECT_RESOLVER'] must be a callable or dotted path."
        )
    return resolver(request)


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
    Supports ordering by rating, date, or title.
    """
    form = MemeTemplateSearchForm(request.GET)
    query = request.GET.get('q', '').strip()
    order_by = request.GET.get('order', '-created')  # Default: newest first
    
    # Valid ordering options
    valid_orders = ['rating', '-rating', 'created', '-created', 'title', '-title']
    if order_by not in valid_orders:
        order_by = '-created'
    
    templates = MemeTemplate.search(query, order_by=order_by)
    linked_obj = resolve_linked_object(request)
    if linked_obj:
        linked_ids = MemeTemplate.objects.linked_to(linked_obj).values_list('pk', flat=True)
        templates = templates.filter(pk__in=linked_ids)
    
    context = {
        'templates': templates,
        'search_form': form,
        'query': query,
        'order_by': order_by,
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
    - Star rating widget
    """
    template = get_object_or_404(MemeTemplate, pk=pk)
    
    # Get recent memes made from this template
    recent_memes = template.memes.all()[:6]
    
    # Check if user has already rated this template
    user_rating = None
    if request.session.session_key:
        try:
            user_rating = TemplateRating.objects.get(
                template=template,
                session_key=request.session.session_key
            ).stars
        except TemplateRating.DoesNotExist:
            pass
    
    context = {
        'template': template,
        'recent_memes': recent_memes,
        'user_rating': user_rating,
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
            linked_obj = resolve_linked_object(request)
            if linked_obj:
                template.link_to(linked_obj)
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
            linked_obj = resolve_linked_object(request)
            if linked_obj:
                meme.link_to(linked_obj)
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
    Includes star rating widget.
    """
    meme = get_object_or_404(Meme, pk=pk)
    
    # Check if user has already rated this meme
    user_rating = None
    if request.session.session_key:
        try:
            user_rating = MemeRating.objects.get(
                meme=meme,
                session_key=request.session.session_key
            ).stars
        except MemeRating.DoesNotExist:
            pass
    
    context = {
        'meme': meme,
        'user_rating': user_rating,
        'title': f'Meme #{meme.pk}',
        'page_type': 'meme_detail',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/meme_detail.html', context)


def meme_list(request):
    """
    View to display all memes.
    Supports ordering by rating, date.
    """
    order_by = request.GET.get('order', '-created')  # Default: newest first
    
    # Valid ordering options
    valid_orders = ['rating', '-rating', 'created', '-created']
    if order_by not in valid_orders:
        order_by = '-created'
    
    linked_obj = resolve_linked_object(request)
    if linked_obj:
        memes = Meme.objects.linked_to(linked_obj)
    else:
        memes = Meme.objects.all()
    
    # Apply ordering
    if order_by == 'rating' or order_by == '-rating':
        from django.db.models import Case, When, F, FloatField, Value
        from django.db.models.functions import Cast
        
        memes = memes.annotate(
            avg_rating=Case(
                When(rating_count=0, then=Value(0.0)),
                default=Cast(F('rating_sum'), FloatField()) / Cast(F('rating_count'), FloatField()),
                output_field=FloatField()
            )
        )
        if order_by == '-rating':
            memes = memes.order_by('-avg_rating', '-rating_count', '-created_at')
        else:
            memes = memes.order_by('avg_rating', 'rating_count', 'created_at')
    elif order_by == 'created':
        memes = memes.order_by('created_at')
    else:  # -created
        memes = memes.order_by('-created_at')
    
    context = {
        'memes': memes,
        'order_by': order_by,
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
# RATING VIEWS
# =============================================================================

def _ensure_session(request):
    """Ensure the request has a session key."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


@require_POST
def rate_template(request, pk):
    """
    AJAX endpoint to rate a template.
    
    POST data: { "stars": 1-5 }
    Returns: { "success": true, "average_rating": X.X, "rating_count": N, "user_rating": N }
    """
    template = get_object_or_404(MemeTemplate, pk=pk)
    
    try:
        data = json.loads(request.body)
        stars = int(data.get('stars', 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    if not 1 <= stars <= 5:
        return JsonResponse({'success': False, 'error': 'Rating must be 1-5'}, status=400)
    
    session_key = _ensure_session(request)
    
    # Check for existing rating
    try:
        existing = TemplateRating.objects.get(template=template, session_key=session_key)
        old_stars = existing.stars
        existing.stars = stars
        existing.save()
        # Update aggregate: remove old, add new
        template.update_rating(old_stars, stars)
    except TemplateRating.DoesNotExist:
        # Create new rating
        TemplateRating.objects.create(
            template=template,
            session_key=session_key,
            stars=stars
        )
        template.add_rating(stars)
    
    return JsonResponse({
        'success': True,
        'average_rating': template.get_average_rating(),
        'rating_count': template.rating_count,
        'user_rating': stars,
        'rating_display': template.get_rating_display(),
    })


@require_POST
def rate_meme(request, pk):
    """
    AJAX endpoint to rate a meme.
    
    POST data: { "stars": 1-5 }
    Returns: { "success": true, "average_rating": X.X, "rating_count": N, "user_rating": N }
    """
    meme = get_object_or_404(Meme, pk=pk)
    
    try:
        data = json.loads(request.body)
        stars = int(data.get('stars', 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    if not 1 <= stars <= 5:
        return JsonResponse({'success': False, 'error': 'Rating must be 1-5'}, status=400)
    
    session_key = _ensure_session(request)
    
    # Check for existing rating
    try:
        existing = MemeRating.objects.get(meme=meme, session_key=session_key)
        old_stars = existing.stars
        existing.stars = stars
        existing.save()
        # Update aggregate: remove old, add new
        meme.update_rating(old_stars, stars)
    except MemeRating.DoesNotExist:
        # Create new rating
        MemeRating.objects.create(
            meme=meme,
            session_key=session_key,
            stars=stars
        )
        meme.add_rating(stars)
    
    return JsonResponse({
        'success': True,
        'average_rating': meme.get_average_rating(),
        'rating_count': meme.rating_count,
        'user_rating': stars,
        'rating_display': meme.get_rating_display(),
    })


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
            linked_obj = resolve_linked_object(request)
            if linked_obj:
                meme.link_to(linked_obj)
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
            qs = MemeTemplate.search(query)
        else:
            qs = MemeTemplate.objects.all()
        linked_obj = resolve_linked_object(self.request)
        if linked_obj:
            linked_ids = MemeTemplate.objects.linked_to(linked_obj).values_list('pk', flat=True)
            qs = qs.filter(pk__in=linked_ids)
        return qs
    
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
        linked_obj = resolve_linked_object(self.request)
        if linked_obj:
            self.object.link_to(linked_obj)
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
        response = super().form_valid(form)
        linked_obj = resolve_linked_object(self.request)
        if linked_obj:
            self.object.link_to(linked_obj)
        messages.success(self.request, 'Meme created successfully!')
        return response


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

    def get_queryset(self):
        linked_obj = resolve_linked_object(self.request)
        if linked_obj:
            return Meme.objects.linked_to(linked_obj)
        return Meme.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'All Memes'
        context['page_type'] = 'meme_list'
        context.update(get_meme_maker_context())
        return context


# Need to import reverse for CBV success_url
from django.urls import reverse
