from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.views.generic import CreateView, DetailView, ListView

from .models import Meme
from .forms import MemeForm
from .conf import meme_maker_settings


def get_meme_maker_context():
    """Get the meme maker configuration context for templates."""
    return meme_maker_settings.get_context()


def home(request):
    """Home page view - redirects to create meme."""
    return redirect('meme_maker:create')


def create_meme(request):
    """View to create a new meme."""
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save()
            messages.success(request, 'Meme created successfully!')
            return redirect('meme_maker:detail', pk=meme.pk)
    else:
        form = MemeForm()
    
    context = {
        'form': form,
        'title': 'Create Meme',
        'page_type': 'create',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/create.html', context)


def meme_detail(request, pk):
    """View to display a single meme."""
    meme = get_object_or_404(Meme, pk=pk)
    
    context = {
        'meme': meme,
        'title': f'Meme #{meme.pk}',
        'page_type': 'detail',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/detail.html', context)


def meme_list(request):
    """View to display all memes."""
    memes = Meme.objects.all()
    
    context = {
        'memes': memes,
        'title': 'All Memes',
        'page_type': 'list',
    }
    context.update(get_meme_maker_context())
    
    return render(request, 'meme_maker/list.html', context)


# Class-based views for more flexibility
class MemeCreateView(CreateView):
    """Class-based view for creating memes."""
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
    template_name = 'meme_maker/detail.html'
    context_object_name = 'meme'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Meme #{self.object.pk}'
        context['page_type'] = 'detail'
        context.update(get_meme_maker_context())
        return context


class MemeListView(ListView):
    """Class-based view for listing all memes."""
    model = Meme
    template_name = 'meme_maker/list.html'
    context_object_name = 'memes'
    paginate_by = 12
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'All Memes'
        context['page_type'] = 'list'
        context.update(get_meme_maker_context())
        return context
