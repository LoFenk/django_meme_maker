"""
Forms for django-meme-maker.

Provides forms for:
- MemeTemplateForm: Uploading new meme templates
- MemeTemplateSearchForm: Searching templates
- MemeEditorForm: Creating memes from templates with text overlays
- MemeForm: Legacy form for direct meme creation (backward compatibility)
"""

import json
from django import forms
from .models import Meme, MemeTemplate


class MemeTemplateForm(forms.ModelForm):
    """
    Form for uploading a new meme template.
    
    Users provide an image, title, and optional tags.
    Tags can be entered as a comma-separated string.
    """
    
    class Meta:
        model = MemeTemplate
        fields = ['image', 'title', 'tags']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'meme-form-control',
                'accept': 'image/*'
            }),
            'title': forms.TextInput(attrs={
                'class': 'meme-form-control',
                'placeholder': 'Enter a descriptive title (e.g., "Distracted Boyfriend")',
                'maxlength': '200',
                'required': True,
            }),
            'tags': forms.TextInput(attrs={
                'class': 'meme-form-control',
                'placeholder': 'Enter tags separated by commas (e.g., funny, reaction, trending)',
                'maxlength': '500',
            }),
        }
        labels = {
            'image': 'Template Image',
            'title': 'Title',
            'tags': 'Tags',
        }
        help_texts = {
            'image': 'Upload the base image for your meme template',
            'title': 'A searchable name for this template',
            'tags': 'Comma-separated keywords to help others find this template',
        }


class MemeTemplateSearchForm(forms.Form):
    """
    Form for searching meme templates.
    
    Searches across title and tags.
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'meme-form-control',
            'placeholder': 'Search templates by name or tags...',
            'autocomplete': 'off',
        }),
        label='Search',
    )


class MemeEditorForm(forms.Form):
    """
    Form for creating a meme from a template.
    
    Handles text overlay configuration as JSON.
    Provides both simple (top/bottom) and advanced (custom position) modes.
    """
    
    # Simple mode - top and bottom text
    top_text = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'meme-form-control meme-editor-text',
            'placeholder': 'Top text (optional)',
            'data-position': 'top',
        }),
        label='Top Text',
    )
    
    bottom_text = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'meme-form-control meme-editor-text',
            'placeholder': 'Bottom text (optional)',
            'data-position': 'bottom',
        }),
        label='Bottom Text',
    )
    
    # Advanced mode - full JSON configuration
    # Hidden field populated by JavaScript for advanced editor
    text_overlays_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'text-overlays-json',
        }),
    )
    
    # Text styling options
    text_color = forms.CharField(
        required=False,
        initial='#FFFFFF',
        widget=forms.TextInput(attrs={
            'class': 'meme-form-control meme-color-picker',
            'type': 'color',
        }),
        label='Text Color',
    )
    
    stroke_color = forms.CharField(
        required=False,
        initial='#000000',
        widget=forms.TextInput(attrs={
            'class': 'meme-form-control meme-color-picker',
            'type': 'color',
        }),
        label='Stroke Color',
    )
    
    font_size = forms.IntegerField(
        required=False,
        initial=48,
        min_value=12,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'meme-form-control',
            'type': 'range',
            'min': '12',
            'max': '200',
        }),
        label='Font Size',
    )
    
    uppercase = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'meme-checkbox',
        }),
        label='UPPERCASE',
    )
    
    def get_overlays(self):
        """
        Convert form data to text overlays list.
        
        If JSON is provided (advanced mode), use that.
        Otherwise, build from simple top/bottom fields.
        """
        json_data = self.cleaned_data.get('text_overlays_json')
        
        if json_data:
            try:
                data = json.loads(json_data)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'overlays' in data:
                    return data['overlays']
            except json.JSONDecodeError:
                pass
        
        # Build from simple fields
        overlays = []
        
        text_color = self.cleaned_data.get('text_color', '#FFFFFF')
        stroke_color = self.cleaned_data.get('stroke_color', '#000000')
        font_size = self.cleaned_data.get('font_size', 48)
        uppercase = self.cleaned_data.get('uppercase', True)
        
        top_text = self.cleaned_data.get('top_text', '').strip()
        if top_text:
            overlays.append({
                'text': top_text,
                'position': 'top',
                'color': text_color,
                'stroke_color': stroke_color,
                'font_size': font_size,
                'uppercase': uppercase,
            })
        
        bottom_text = self.cleaned_data.get('bottom_text', '').strip()
        if bottom_text:
            overlays.append({
                'text': bottom_text,
                'position': 'bottom',
                'color': text_color,
                'stroke_color': stroke_color,
                'font_size': font_size,
                'uppercase': uppercase,
            })
        
        return overlays


# Legacy forms for backward compatibility
class MemeForm(forms.ModelForm):
    """
    Legacy form for creating memes with direct image upload.
    
    Kept for backward compatibility with existing integrations.
    For new memes, use MemeEditorForm with templates instead.
    """
    
    class Meta:
        model = Meme
        fields = ['image', 'top_text', 'bottom_text']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'meme-form-control',
                'accept': 'image/*'
            }),
            'top_text': forms.TextInput(attrs={
                'class': 'meme-form-control',
                'placeholder': 'Enter top text (optional)',
                'maxlength': '200'
            }),
            'bottom_text': forms.TextInput(attrs={
                'class': 'meme-form-control',
                'placeholder': 'Enter bottom text (optional)',
                'maxlength': '200'
            }),
        }
        labels = {
            'image': 'Upload Image',
            'top_text': 'Top Text',
            'bottom_text': 'Bottom Text',
        }
        help_texts = {
            'image': 'Select an image file for your meme',
            'top_text': 'Text displayed at the top of the image',
            'bottom_text': 'Text displayed at the bottom of the image',
        }


class MemeEditForm(MemeForm):
    """
    Form for editing existing memes.
    Makes the image field optional since one already exists.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['image'].help_text = 'Leave empty to keep the current image'
