"""
Views for django-meme-maker.

Provides views for:
- Template bank (search, list, detail, upload)
- Meme editor (create memes from templates)
- Meme display and download
- Rating system for templates and memes
"""

import json
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, DetailView, ListView
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Meme, MemeTemplate, TemplateRating, MemeRating, MemeFlag, TemplateFlag
from .forms import MemeTemplateForm, MemeTemplateSearchForm, MemeEditorForm
from .conf import meme_maker_settings


def get_meme_maker_context():
    """Get the meme maker configuration context for templates."""
    return meme_maker_settings.get_context()

def resolve_linked_object(request):
    """Resolve a linked object for scoping templates/memes, if configured."""
    if hasattr(request, '_meme_maker_linked_object'):
        return request._meme_maker_linked_object
    resolver = meme_maker_settings.LINKED_OBJECT_RESOLVER
    if not resolver:
        request._meme_maker_linked_object = None
        return None
    if isinstance(resolver, str):
        resolver = import_string(resolver)
    if not callable(resolver):
        raise ImproperlyConfigured(
            "MEME_MAKER['LINKED_OBJECT_RESOLVER'] must be a callable or dotted path."
        )
    request._meme_maker_linked_object = resolver(request)
    return request._meme_maker_linked_object


def get_per_page(request, default=25):
    """Get validated per-page value from query params."""
    allowed = {10, 25, 50}
    try:
        per_page = int(request.GET.get('per_page', default))
    except (TypeError, ValueError):
        per_page = default
    return per_page if per_page in allowed else default


def get_redirect_back(request, fallback_url_name, **kwargs):
    """Return a safe fallback redirect URL."""
    return request.META.get('HTTP_REFERER') or reverse(fallback_url_name, kwargs=kwargs or None)


def get_template_candidates(template_name):
    """Return themed template candidates with fallback."""
    template_set = meme_maker_settings.TEMPLATE_SET
    if not template_set:
        return [template_name]
    base_name = template_name
    if template_name.startswith('meme_maker/'):
        base_name = template_name[len('meme_maker/'):]
    themed = f"meme_maker/{template_set}/{base_name}"
    return [themed, template_name]


def get_template_memes_queryset(template, linked_obj=None):
    qs = template.memes.filter(flagged=False)
    if linked_obj:
        qs = qs.filter(
            pk__in=Meme.objects.linked_to(linked_obj).values_list('pk', flat=True)
        )
    return qs


def apply_template_memes_sort(qs, sort_key):
    sort_key = (sort_key or 'recent').lower()
    if sort_key == 'random':
        return qs.order_by('?'), sort_key

    from django.db.models import Case, When, F, FloatField, Value
    from django.db.models.functions import Cast
    qs = qs.annotate(
        avg_rating=Case(
            When(rating_count=0, then=Value(0.0)),
            default=Cast(F('rating_sum'), FloatField()) / Cast(F('rating_count'), FloatField()),
            output_field=FloatField()
        )
    )

    if sort_key == 'best':
        qs = qs.filter(rating_count__gte=5).order_by('-avg_rating', '-rating_count', '-created_at')
    elif sort_key == 'popular':
        qs = qs.filter(avg_rating__gte=3.0).order_by('-rating_count', '-avg_rating', '-created_at')
    elif sort_key == 'worst':
        qs = qs.filter(rating_count__gt=0).order_by('avg_rating', 'rating_count', 'created_at')
    else:
        sort_key = 'recent'
        qs = qs.order_by('-created_at')
    return qs, sort_key


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
    per_page = get_per_page(request, default=25)
    
    # Valid ordering options
    valid_orders = ['rating', '-rating', 'created', '-created', 'title', '-title']
    if order_by not in valid_orders:
        order_by = '-created'
    
    templates = MemeTemplate.search(query, order_by=order_by).filter(flagged=False)
    from django.db.models import Count, Q
    templates = templates.annotate(
        unflagged_meme_count=Count('memes', filter=Q(memes__flagged=False))
    )
    linked_obj = resolve_linked_object(request)
    if linked_obj:
        linked_ids = MemeTemplate.objects.linked_to(linked_obj).values_list('pk', flat=True)
        templates = templates.filter(pk__in=linked_ids)

    paginator = Paginator(templates, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'templates': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'total_count': paginator.count,
        'search_form': form,
        'query': query,
        'order_by': order_by,
        'per_page': per_page,
        'title': 'Template Bank',
        'page_type': 'template_list',
    }
    context.update(get_meme_maker_context())
    
    return render(request, get_template_candidates('meme_maker/template_list.html'), context)


def template_detail(request, pk):
    """
    Template detail page.
    
    Shows the template image and provides:
    - Download template button
    - "Make my own" button → links to meme editor
    - Star rating widget
    """
    from django.db.models import Count, Q
    template = get_object_or_404(
        MemeTemplate.objects.annotate(
            unflagged_meme_count=Count('memes', filter=Q(memes__flagged=False))
        ),
        pk=pk,
    )
    if template.flagged:
        raise Http404
    linked_obj = resolve_linked_object(request)
    if linked_obj and not template.is_linked_to(linked_obj):
        raise Http404
    
    sort_key = request.GET.get('sort', 'recent')
    memes_qs = get_template_memes_queryset(template, linked_obj=linked_obj)
    memes_qs, sort_key = apply_template_memes_sort(memes_qs, sort_key)
    recent_memes = memes_qs[:6]
    
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
        'memes_sort': sort_key,
        'user_rating': user_rating,
        'title': template.title,
        'page_type': 'template_detail',
    }
    context.update(get_meme_maker_context())
    
    return render(request, get_template_candidates('meme_maker/template_detail.html'), context)


def template_memes_partial(request, pk):
    template = get_object_or_404(MemeTemplate, pk=pk)
    if template.flagged:
        raise Http404
    linked_obj = resolve_linked_object(request)
    if linked_obj and not template.is_linked_to(linked_obj):
        raise Http404

    sort_key = request.GET.get('sort', 'recent')
    memes_qs = get_template_memes_queryset(template, linked_obj=linked_obj)
    memes_qs, sort_key = apply_template_memes_sort(memes_qs, sort_key)
    context = {
        'template': template,
        'recent_memes': memes_qs[:6],
        'memes_sort': sort_key,
    }
    return render(request, get_template_candidates('meme_maker/partials/template_memes.html'), context)


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
    
    return render(request, get_template_candidates('meme_maker/template_upload.html'), context)


def template_download(request, pk):
    """
    Download a template image.
    
    Returns the template image file as a download.
    """
    template = get_object_or_404(MemeTemplate, pk=pk, flagged=False)
    linked_obj = resolve_linked_object(request)
    if linked_obj and not template.is_linked_to(linked_obj):
        raise Http404
    
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
    template = get_object_or_404(MemeTemplate, pk=template_pk, flagged=False)
    
    if request.method == 'POST':
        form = MemeEditorForm(request.POST)
        if form.is_valid():
            # Create new meme from template
            meme = Meme(template=template)
            
            # Get overlays and meta (preview dimensions) from form
            overlays, meta = form.get_overlays_with_meta()
            meme.set_overlays(overlays, meta)
            
            meme.nsfw = form.cleaned_data.get('nsfw', False)
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
    
    return render(request, get_template_candidates('meme_maker/meme_editor.html'), context)


# =============================================================================
# MEME VIEWS
# =============================================================================

def meme_detail(request, pk):
    """
    View to display a single meme.
    
    Shows the meme with text overlays and provides download option.
    Includes star rating widget.
    """
    meme = get_object_or_404(Meme, pk=pk, flagged=False)
    linked_obj = resolve_linked_object(request)
    if linked_obj and not meme.is_linked_to(linked_obj):
        raise Http404
    
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
    
    return render(request, get_template_candidates('meme_maker/meme_detail.html'), context)


def meme_list(request):
    """
    View to display all memes.
    Supports ordering by rating, date.
    """
    order_by = request.GET.get('order', '-created')  # Default: newest first
    per_page = get_per_page(request, default=25)
    
    # Valid ordering options
    valid_orders = ['rating', '-rating', 'created', '-created']
    if order_by not in valid_orders:
        order_by = '-created'
    
    linked_obj = resolve_linked_object(request)
    if linked_obj:
        memes = Meme.objects.linked_to(linked_obj)
    else:
        memes = Meme.objects.all()
    memes = memes.filter(flagged=False)
    
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
    
    paginator = Paginator(memes, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'memes': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'total_count': paginator.count,
        'order_by': order_by,
        'per_page': per_page,
        'title': 'All Memes',
        'page_type': 'meme_list',
    }
    context.update(get_meme_maker_context())
    
    return render(request, get_template_candidates('meme_maker/meme_list.html'), context)


def meme_download(request, pk):
    """
    Download a meme image.
    
    Returns the generated composite image if available,
    otherwise returns the source image.
    """
    meme = get_object_or_404(Meme, pk=pk)
    linked_obj = resolve_linked_object(request)
    if linked_obj and not meme.is_linked_to(linked_obj):
        raise Http404
    
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


def _user_flag_count_today(user):
    today = timezone.localdate()
    return (
        TemplateFlag.objects.filter(user=user, created_at__date=today).count() +
        MemeFlag.objects.filter(user=user, created_at__date=today).count()
    )


@require_POST
def rate_template(request, pk):
    """
    AJAX endpoint to rate a template.
    
    POST data: { "stars": 1-5 }
    Returns: { "success": true, "average_rating": X.X, "rating_count": N, "user_rating": N }
    """
    template = get_object_or_404(MemeTemplate, pk=pk, flagged=False)
    linked_obj = resolve_linked_object(request)
    if linked_obj and not template.is_linked_to(linked_obj):
        raise Http404
    
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
    meme = get_object_or_404(Meme, pk=pk, flagged=False)
    linked_obj = resolve_linked_object(request)
    if linked_obj and not meme.is_linked_to(linked_obj):
        raise Http404
    
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
# FLAGGING VIEWS
# =============================================================================

@login_required
@require_POST
def flag_template(request, pk):
    template = get_object_or_404(MemeTemplate, pk=pk)
    if template.flagged:
        messages.info(request, 'This template is already flagged for review.')
        return redirect(get_redirect_back(request, 'meme_maker:template_list'))
    if TemplateFlag.objects.filter(template=template, user=request.user).exists():
        messages.info(request, 'You already flagged this template.')
        return redirect(get_redirect_back(request, 'meme_maker:template_detail', pk=template.pk))
    if _user_flag_count_today(request.user) >= 5:
        messages.error(request, 'Daily flag limit reached. Please contact an admin if you need more removed.')
        return redirect(get_redirect_back(request, 'meme_maker:template_detail', pk=template.pk))

    TemplateFlag.objects.create(template=template, user=request.user)
    template.flagged = True
    template.flagged_at = timezone.now()
    template.save(update_fields=['flagged', 'flagged_at'])
    messages.success(request, 'Thanks for the report. This template is now flagged for review.')
    return redirect(get_redirect_back(request, 'meme_maker:template_list'))


@login_required
@require_POST
def flag_meme(request, pk):
    meme = get_object_or_404(Meme, pk=pk)
    if meme.flagged:
        messages.info(request, 'This meme is already flagged for review.')
        return redirect(get_redirect_back(request, 'meme_maker:meme_list'))
    if MemeFlag.objects.filter(meme=meme, user=request.user).exists():
        messages.info(request, 'You already flagged this meme.')
        return redirect(get_redirect_back(request, 'meme_maker:meme_detail', pk=meme.pk))
    if _user_flag_count_today(request.user) >= 5:
        messages.error(request, 'Daily flag limit reached. Please contact an admin if you need more removed.')
        return redirect(get_redirect_back(request, 'meme_maker:meme_detail', pk=meme.pk))

    MemeFlag.objects.create(meme=meme, user=request.user)
    meme.flagged = True
    meme.flagged_at = timezone.now()
    meme.save(update_fields=['flagged', 'flagged_at'])
    messages.success(request, 'Thanks for the report. This meme is now flagged for review.')
    return redirect(get_redirect_back(request, 'meme_maker:meme_list'))


# =============================================================================
# CLASS-BASED VIEWS
# =============================================================================

class MemeTemplateListView(ListView):
    """Class-based view for template list with search."""
    model = MemeTemplate
    template_name = 'meme_maker/template_list.html'
    context_object_name = 'templates'
    paginate_by = 25

    def get_paginate_by(self, queryset):
        return get_per_page(self.request, default=self.paginate_by)
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = MemeTemplate.search(query)
        else:
            qs = MemeTemplate.objects.all()
        qs = qs.filter(flagged=False)
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
        context['per_page'] = self.get_paginate_by(self.get_queryset())
        if 'paginator' in context:
            context['total_count'] = context['paginator'].count
        context.update(get_meme_maker_context())
        return context

    def get_template_names(self):
        return get_template_candidates(self.template_name)


class MemeTemplateDetailView(DetailView):
    """Class-based view for template detail."""
    model = MemeTemplate
    template_name = 'meme_maker/template_detail.html'
    context_object_name = 'template'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        linked_obj = resolve_linked_object(self.request)
        if self.object.flagged:
            raise Http404
        if linked_obj and not self.object.is_linked_to(linked_obj):
            raise Http404
        recent_memes = self.object.memes.filter(flagged=False)
        if linked_obj:
            recent_memes = recent_memes.filter(
                pk__in=Meme.objects.linked_to(linked_obj).values_list('pk', flat=True)
            )
        context['recent_memes'] = recent_memes[:6]
        context['title'] = self.object.title
        context['page_type'] = 'template_detail'
        context.update(get_meme_maker_context())
        return context

    def get_template_names(self):
        return get_template_candidates(self.template_name)


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

    def get_template_names(self):
        return get_template_candidates(self.template_name)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        linked_obj = resolve_linked_object(self.request)
        if linked_obj:
            self.object.link_to(linked_obj)
        messages.success(self.request, f'Template "{self.object.title}" uploaded successfully!')
        return response
    
    def get_success_url(self):
        return reverse('meme_maker:meme_editor', kwargs={'template_pk': self.object.pk})


class MemeDetailView(DetailView):
    """Class-based view for viewing a single meme."""
    model = Meme
    template_name = 'meme_maker/meme_detail.html'
    context_object_name = 'meme'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        linked_obj = resolve_linked_object(self.request)
        if self.object.flagged:
            raise Http404
        if linked_obj and not self.object.is_linked_to(linked_obj):
            raise Http404
        context['title'] = f'Meme #{self.object.pk}'
        context['page_type'] = 'meme_detail'
        context.update(get_meme_maker_context())
        return context

    def get_template_names(self):
        return get_template_candidates(self.template_name)


class MemeListView(ListView):
    """Class-based view for listing all memes."""
    model = Meme
    template_name = 'meme_maker/meme_list.html'
    context_object_name = 'memes'
    paginate_by = 25

    def get_paginate_by(self, queryset):
        return get_per_page(self.request, default=self.paginate_by)

    def get_queryset(self):
        linked_obj = resolve_linked_object(self.request)
        if linked_obj:
            qs = Meme.objects.linked_to(linked_obj)
        else:
            qs = Meme.objects.all()
        return qs.filter(flagged=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'All Memes'
        context['page_type'] = 'meme_list'
        context['per_page'] = self.get_paginate_by(self.get_queryset())
        if 'paginator' in context:
            context['total_count'] = context['paginator'].count
        context.update(get_meme_maker_context())
        return context

    def get_template_names(self):
        return get_template_candidates(self.template_name)


# Need to import reverse for CBV success_url
from django.urls import reverse
