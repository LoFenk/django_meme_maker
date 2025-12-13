from django import forms
from .models import Meme


class MemeForm(forms.ModelForm):
    """
    Form for creating memes.
    
    Uses custom CSS classes that work with the meme maker's built-in styles.
    Can be customized by overriding widget attributes or extending this form.
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
        # Make image optional when editing
        self.fields['image'].required = False
        self.fields['image'].help_text = 'Leave empty to keep the current image'
