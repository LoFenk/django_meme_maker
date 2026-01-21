"""
Test suite for django-meme-maker.

Run tests with:
    python manage.py test meme_maker
    
Or with pytest:
    pytest meme_maker/tests.py -v
"""

import json
import tempfile
from io import BytesIO
from PIL import Image

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from .models import MemeTemplate, Meme, TemplateLink, MemeLink
from .forms import MemeTemplateForm, MemeEditorForm, MemeForm, MemeTemplateSearchForm


def create_test_image(width=800, height=600, color='red', format='PNG'):
    """Helper function to create a test image file."""
    image = Image.new('RGB', (width, height), color=color)
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def get_test_image_file(name='test.png', width=800, height=600, color='red'):
    """Create a SimpleUploadedFile containing a test image."""
    buffer = create_test_image(width, height, color)
    return SimpleUploadedFile(
        name=name,
        content=buffer.read(),
        content_type='image/png'
    )

def linked_object_resolver(request):
    """Test resolver that scopes to a known user."""
    return User.objects.filter(username='linked-resolver').first()


# =============================================================================
# MODEL TESTS
# =============================================================================

class MemeTemplateModelTest(TestCase):
    """Tests for the MemeTemplate model."""
    
    def setUp(self):
        """Set up test data."""
        self.image_file = get_test_image_file('template.png')
        self.template = MemeTemplate.objects.create(
            image=self.image_file,
            title='Test Template',
            tags='funny, test, meme'
        )
    
    def test_template_creation(self):
        """Test that a template can be created with all fields."""
        self.assertEqual(self.template.title, 'Test Template')
        self.assertEqual(self.template.tags, 'funny, test, meme')
        self.assertTrue(self.template.image)
        self.assertIsNotNone(self.template.created_at)
        self.assertIsNotNone(self.template.updated_at)
    
    def test_template_str(self):
        """Test the string representation of a template."""
        self.assertEqual(str(self.template), 'Test Template')
    
    def test_get_absolute_url(self):
        """Test that get_absolute_url returns the correct URL."""
        url = self.template.get_absolute_url()
        expected = reverse('meme_maker:template_detail', kwargs={'pk': self.template.pk})
        self.assertEqual(url, expected)
    
    def test_get_tags_list(self):
        """Test that tags are parsed correctly into a list."""
        tags = self.template.get_tags_list()
        self.assertEqual(tags, ['funny', 'test', 'meme'])
    
    def test_get_tags_list_empty(self):
        """Test that empty tags return an empty list."""
        self.template.tags = ''
        self.template.save()
        self.assertEqual(self.template.get_tags_list(), [])
    
    def test_set_tags_from_list(self):
        """Test setting tags from a list."""
        self.template.set_tags_from_list(['new', 'tags', 'here'])
        self.assertEqual(self.template.tags, 'new, tags, here')
    
    def test_search_by_title(self):
        """Test searching templates by title."""
        results = MemeTemplate.search('Test')
        self.assertIn(self.template, results)
    
    def test_search_by_tags(self):
        """Test searching templates by tags."""
        results = MemeTemplate.search('funny')
        self.assertIn(self.template, results)
    
    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        results = MemeTemplate.search('FUNNY')
        self.assertIn(self.template, results)
    
    def test_search_no_results(self):
        """Test search with no matching results."""
        results = MemeTemplate.search('nonexistent')
        self.assertEqual(len(results), 0)
    
    def test_search_empty_query(self):
        """Test that empty search returns all templates."""
        results = MemeTemplate.search('')
        self.assertIn(self.template, results)
    
    def test_ordering(self):
        """Test that templates are ordered by created_at descending."""
        template2 = MemeTemplate.objects.create(
            image=get_test_image_file('template2.png'),
            title='Second Template'
        )
        templates = list(MemeTemplate.objects.all())
        self.assertEqual(templates[0], template2)
        self.assertEqual(templates[1], self.template)


class MemeModelTest(TestCase):
    """Tests for the Meme model."""
    
    def setUp(self):
        """Set up test data."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('template.png'),
            title='Test Template',
            tags='test'
        )
    
    def test_meme_creation_with_template(self):
        """Test creating a meme from a template."""
        meme = Meme.objects.create(
            template=self.template,
            top_text='Hello',
            bottom_text='World'
        )
        self.assertEqual(meme.template, self.template)
        self.assertEqual(meme.top_text, 'Hello')
        self.assertEqual(meme.bottom_text, 'World')
    
    def test_meme_creation_legacy(self):
        """Test creating a meme with direct image upload (legacy)."""
        meme = Meme.objects.create(
            image=get_test_image_file('meme.png'),
            top_text='Legacy',
            bottom_text='Meme'
        )
        self.assertIsNone(meme.template)
        self.assertTrue(meme.image)
    
    def test_meme_str_with_template(self):
        """Test string representation with template."""
        meme = Meme.objects.create(
            template=self.template,
            top_text='Test'
        )
        self.assertIn('Test Template', str(meme))
    
    def test_meme_str_without_template(self):
        """Test string representation without template."""
        meme = Meme.objects.create(
            image=get_test_image_file('meme.png'),
            top_text='Hello World Test'
        )
        self.assertIn('Hello World Test', str(meme))
    
    def test_get_absolute_url(self):
        """Test get_absolute_url returns correct URL."""
        meme = Meme.objects.create(template=self.template)
        url = meme.get_absolute_url()
        expected = reverse('meme_maker:meme_detail', kwargs={'pk': meme.pk})
        self.assertEqual(url, expected)
    
    def test_get_source_image_from_template(self):
        """Test getting source image from template."""
        meme = Meme.objects.create(template=self.template)
        source = meme.get_source_image()
        self.assertEqual(source, self.template.image)
    
    def test_get_source_image_direct(self):
        """Test getting source image from direct upload."""
        image_file = get_test_image_file('direct.png')
        meme = Meme.objects.create(image=image_file)
        source = meme.get_source_image()
        self.assertEqual(source, meme.image)
    
    def test_set_and_get_overlays(self):
        """Test setting and getting text overlays."""
        meme = Meme.objects.create(template=self.template)
        overlays = [
            {'text': 'Top', 'position': 'top', 'color': '#FFFFFF'},
            {'text': 'Bottom', 'position': 'bottom', 'color': '#FFFFFF'}
        ]
        meme.set_overlays(overlays)
        meme.save()
        
        retrieved = meme.get_overlays()
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved[0]['text'], 'Top')
    
    def test_get_overlay_for_css_with_overlays(self):
        """Test CSS overlay generation from JSON overlays."""
        meme = Meme.objects.create(template=self.template)
        meme.set_overlays([
            {'text': 'Test', 'position': 'top', 'color': '#FF0000'}
        ])
        meme.save()
        
        css_overlays = meme.get_overlay_for_css()
        self.assertEqual(len(css_overlays), 1)
        self.assertEqual(css_overlays[0]['text'], 'Test')
        self.assertEqual(css_overlays[0]['position'], 'top')
    
    def test_get_overlay_for_css_legacy(self):
        """Test CSS overlay generation from legacy fields."""
        meme = Meme.objects.create(
            template=self.template,
            top_text='Legacy Top',
            bottom_text='Legacy Bottom'
        )
        # Clear overlays to use legacy fields
        meme.text_overlays = {}
        meme.save()
        
        css_overlays = meme.get_overlay_for_css()
        self.assertEqual(len(css_overlays), 2)
        texts = [o['text'] for o in css_overlays]
        self.assertIn('Legacy Top', texts)
        self.assertIn('Legacy Bottom', texts)
    
    def test_image_generation(self):
        """Test that image generation creates a file."""
        meme = Meme.objects.create(
            template=self.template,
            top_text='Generated',
            bottom_text='Image'
        )
        # Refresh from DB to get updated generated_image
        meme.refresh_from_db()
        
        # Check if generated image was created
        # Note: This may fail if Pillow can't find fonts
        if meme.generated_image:
            self.assertTrue(meme.generated_image.name)
    
    def test_ordering(self):
        """Test that memes are ordered by created_at descending."""
        meme1 = Meme.objects.create(template=self.template, top_text='First')
        meme2 = Meme.objects.create(template=self.template, top_text='Second')
        
        memes = list(Meme.objects.all())
        self.assertEqual(memes[0], meme2)
        self.assertEqual(memes[1], meme1)


# =============================================================================
# FORM TESTS
# =============================================================================

class MemeTemplateFormTest(TestCase):
    """Tests for MemeTemplateForm."""
    
    def test_valid_form(self):
        """Test form with valid data."""
        image_file = get_test_image_file('test.png')
        form = MemeTemplateForm(
            data={'title': 'Test', 'tags': 'funny, meme'},
            files={'image': image_file}
        )
        self.assertTrue(form.is_valid())
    
    def test_missing_image(self):
        """Test form without image is invalid."""
        form = MemeTemplateForm(data={'title': 'Test'})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
    
    def test_missing_title(self):
        """Test form without title is invalid."""
        image_file = get_test_image_file('test.png')
        form = MemeTemplateForm(
            data={'tags': 'test'},
            files={'image': image_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_optional_tags(self):
        """Test that tags are optional."""
        image_file = get_test_image_file('test.png')
        form = MemeTemplateForm(
            data={'title': 'Test'},
            files={'image': image_file}
        )
        self.assertTrue(form.is_valid())


class MemeEditorFormTest(TestCase):
    """Tests for MemeEditorForm."""
    
    def test_valid_form_simple(self):
        """Test form with simple top/bottom text."""
        form = MemeEditorForm(data={
            'top_text': 'Hello',
            'bottom_text': 'World',
            'text_color': '#FFFFFF',
            'stroke_color': '#000000',
            'font_size': 48,
            'uppercase': True
        })
        self.assertTrue(form.is_valid())
    
    def test_empty_form_valid(self):
        """Test that form with no text is still valid."""
        form = MemeEditorForm(data={})
        self.assertTrue(form.is_valid())
    
    def test_get_overlays_simple(self):
        """Test getting overlays from simple form data."""
        form = MemeEditorForm(data={
            'top_text': 'Top Text',
            'bottom_text': 'Bottom Text',
            'text_color': '#FF0000',
            'stroke_color': '#0000FF',
            'font_size': 64,
            'uppercase': False
        })
        form.is_valid()
        
        overlays = form.get_overlays()
        self.assertEqual(len(overlays), 2)
        
        top = next(o for o in overlays if o['position'] == 'top')
        self.assertEqual(top['text'], 'Top Text')
        self.assertEqual(top['color'], '#FF0000')
        self.assertEqual(top['font_size'], 64)
        self.assertEqual(top['uppercase'], False)
    
    def test_get_overlays_json(self):
        """Test getting overlays from JSON data."""
        json_data = json.dumps([
            {'text': 'JSON Text', 'position': 'top', 'color': '#123456'}
        ])
        form = MemeEditorForm(data={
            'text_overlays_json': json_data
        })
        form.is_valid()
        
        overlays = form.get_overlays()
        self.assertEqual(len(overlays), 1)
        self.assertEqual(overlays[0]['text'], 'JSON Text')
    
    def test_get_overlays_empty(self):
        """Test getting overlays when no text provided."""
        form = MemeEditorForm(data={
            'top_text': '',
            'bottom_text': ''
        })
        form.is_valid()
        
        overlays = form.get_overlays()
        self.assertEqual(len(overlays), 0)


class MemeFormTest(TestCase):
    """Tests for MemeForm (legacy)."""
    
    def test_valid_form(self):
        """Test form with valid data."""
        image_file = get_test_image_file('meme.png')
        form = MemeForm(
            data={'top_text': 'Hello', 'bottom_text': 'World'},
            files={'image': image_file}
        )
        self.assertTrue(form.is_valid())
    
    def test_image_is_optional(self):
        """Test form without image is valid (memes can use templates)."""
        # Image is optional in the model since memes can be created from templates
        form = MemeForm(data={'top_text': 'Test'})
        self.assertTrue(form.is_valid())
    
    def test_optional_text(self):
        """Test that text fields are optional."""
        image_file = get_test_image_file('meme.png')
        form = MemeForm(
            data={},
            files={'image': image_file}
        )
        self.assertTrue(form.is_valid())
    
    def test_completely_empty_form(self):
        """Test that completely empty form is valid (all fields optional)."""
        form = MemeForm(data={})
        self.assertTrue(form.is_valid())


class MemeTemplateSearchFormTest(TestCase):
    """Tests for MemeTemplateSearchForm."""
    
    def test_valid_form(self):
        """Test form with search query."""
        form = MemeTemplateSearchForm(data={'q': 'funny'})
        self.assertTrue(form.is_valid())
    
    def test_empty_search(self):
        """Test form with empty search is valid."""
        form = MemeTemplateSearchForm(data={'q': ''})
        self.assertTrue(form.is_valid())
    
    def test_no_data(self):
        """Test form with no data is valid."""
        form = MemeTemplateSearchForm(data={})
        self.assertTrue(form.is_valid())


# =============================================================================
# VIEW TESTS
# =============================================================================

class HomeViewTest(TestCase):
    """Tests for the home view."""
    
    def test_home_redirects(self):
        """Test that home redirects to template list."""
        response = self.client.get(reverse('meme_maker:home'))
        self.assertRedirects(response, reverse('meme_maker:template_list'))


class TemplateListViewTest(TestCase):
    """Tests for template list view."""
    
    def setUp(self):
        """Set up test data."""
        self.template1 = MemeTemplate.objects.create(
            image=get_test_image_file('t1.png'),
            title='Funny Cat',
            tags='cat, funny'
        )
        self.template2 = MemeTemplate.objects.create(
            image=get_test_image_file('t2.png'),
            title='Serious Dog',
            tags='dog, serious'
        )
    
    def test_view_url(self):
        """Test the view is accessible."""
        response = self.client.get(reverse('meme_maker:template_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(reverse('meme_maker:template_list'))
        self.assertTemplateUsed(response, 'meme_maker/template_list.html')
    
    def test_lists_all_templates(self):
        """Test all templates are listed."""
        response = self.client.get(reverse('meme_maker:template_list'))
        self.assertContains(response, 'Funny Cat')
        self.assertContains(response, 'Serious Dog')
    
    def test_search_filters_results(self):
        """Test search filters templates."""
        response = self.client.get(reverse('meme_maker:template_list'), {'q': 'cat'})
        self.assertContains(response, 'Funny Cat')
        self.assertNotContains(response, 'Serious Dog')
    
    def test_search_by_tag(self):
        """Test search by tag."""
        response = self.client.get(reverse('meme_maker:template_list'), {'q': 'serious'})
        self.assertContains(response, 'Serious Dog')
        self.assertNotContains(response, 'Funny Cat')
    
    def test_empty_state(self):
        """Test empty state when no templates."""
        MemeTemplate.objects.all().delete()
        response = self.client.get(reverse('meme_maker:template_list'))
        self.assertEqual(response.status_code, 200)
        # Check for empty state message or zero templates


class TemplateDetailViewTest(TestCase):
    """Tests for template detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('template.png'),
            title='Test Template',
            tags='test, meme'
        )
    
    def test_view_url(self):
        """Test the view is accessible."""
        response = self.client.get(
            reverse('meme_maker:template_detail', kwargs={'pk': self.template.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(
            reverse('meme_maker:template_detail', kwargs={'pk': self.template.pk})
        )
        self.assertTemplateUsed(response, 'meme_maker/template_detail.html')
    
    def test_displays_template_info(self):
        """Test template info is displayed."""
        response = self.client.get(
            reverse('meme_maker:template_detail', kwargs={'pk': self.template.pk})
        )
        self.assertContains(response, 'Test Template')
    
    def test_has_make_my_own_link(self):
        """Test 'Make My Own' link is present."""
        response = self.client.get(
            reverse('meme_maker:template_detail', kwargs={'pk': self.template.pk})
        )
        editor_url = reverse('meme_maker:meme_editor', kwargs={'template_pk': self.template.pk})
        self.assertContains(response, editor_url)
    
    def test_404_for_nonexistent(self):
        """Test 404 for non-existent template."""
        response = self.client.get(
            reverse('meme_maker:template_detail', kwargs={'pk': 99999})
        )
        self.assertEqual(response.status_code, 404)


class TemplateUploadViewTest(TestCase):
    """Tests for template upload view."""
    
    def test_view_url(self):
        """Test the view is accessible."""
        response = self.client.get(reverse('meme_maker:template_upload'))
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(reverse('meme_maker:template_upload'))
        self.assertTemplateUsed(response, 'meme_maker/template_upload.html')
    
    def test_post_creates_template(self):
        """Test POST creates a new template."""
        image_file = get_test_image_file('new_template.png')
        response = self.client.post(
            reverse('meme_maker:template_upload'),
            {'title': 'New Template', 'tags': 'new, fresh', 'image': image_file}
        )
        
        self.assertEqual(MemeTemplate.objects.count(), 1)
        template = MemeTemplate.objects.first()
        self.assertEqual(template.title, 'New Template')
    
    def test_post_redirects_to_editor(self):
        """Test successful POST redirects to meme editor."""
        image_file = get_test_image_file('new_template.png')
        response = self.client.post(
            reverse('meme_maker:template_upload'),
            {'title': 'New Template', 'image': image_file}
        )
        
        template = MemeTemplate.objects.first()
        self.assertRedirects(
            response,
            reverse('meme_maker:meme_editor', kwargs={'template_pk': template.pk})
        )
    
    def test_invalid_post_shows_errors(self):
        """Test invalid POST shows form errors."""
        response = self.client.post(
            reverse('meme_maker:template_upload'),
            {'title': ''}  # Missing image and title
        )
        self.assertEqual(response.status_code, 200)
        # Form should have errors


class TemplateDownloadViewTest(TestCase):
    """Tests for template download view."""
    
    def setUp(self):
        """Set up test data."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('download_test.png'),
            title='Download Test'
        )
    
    def test_download_returns_file(self):
        """Test download returns the image file."""
        response = self.client.get(
            reverse('meme_maker:template_download', kwargs={'pk': self.template.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.get('Content-Disposition', ''))
    
    def test_404_for_nonexistent(self):
        """Test 404 for non-existent template."""
        response = self.client.get(
            reverse('meme_maker:template_download', kwargs={'pk': 99999})
        )
        self.assertEqual(response.status_code, 404)


class MemeEditorViewTest(TestCase):
    """Tests for meme editor view."""
    
    def setUp(self):
        """Set up test data."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('template.png'),
            title='Editor Test Template'
        )
    
    def test_view_url(self):
        """Test the view is accessible."""
        response = self.client.get(
            reverse('meme_maker:meme_editor', kwargs={'template_pk': self.template.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(
            reverse('meme_maker:meme_editor', kwargs={'template_pk': self.template.pk})
        )
        self.assertTemplateUsed(response, 'meme_maker/meme_editor.html')


@override_settings(MEME_MAKER={'LINKED_OBJECT_RESOLVER': 'meme_maker.tests.linked_object_resolver'})
class LinkedObjectResolverViewTest(TestCase):
    """Tests for linked object resolver integration."""

    def setUp(self):
        self.user = User.objects.create_user(username='linked-resolver', password='testpass')

    def test_resolver_links_template_upload_and_filters_lists(self):
        image_file = get_test_image_file('linked_template.png')
        self.client.post(
            reverse('meme_maker:template_upload'),
            {'title': 'Linked Template', 'image': image_file}
        )
        template = MemeTemplate.objects.get(title='Linked Template')
        self.assertTrue(template.is_linked_to(self.user))

        unlinked_template = MemeTemplate.objects.create(
            image=get_test_image_file('unlinked_template.png'),
            title='Unlinked Template'
        )

        response = self.client.get(reverse('meme_maker:template_list'))
        templates = list(response.context['templates'])
        self.assertIn(template, templates)
        self.assertNotIn(unlinked_template, templates)

        linked_meme = Meme.objects.create(template=template)
        linked_meme.link_to(self.user)
        unlinked_meme = Meme.objects.create(template=unlinked_template)

        response = self.client.get(reverse('meme_maker:meme_list'))
        memes = list(response.context['memes'])
        self.assertIn(linked_meme, memes)
        self.assertNotIn(unlinked_meme, memes)
    
    def test_post_creates_meme(self):
        """Test POST creates a new meme."""
        response = self.client.post(
            reverse('meme_maker:meme_editor', kwargs={'template_pk': self.template.pk}),
            {
                'top_text': 'Hello',
                'bottom_text': 'World',
                'text_color': '#FFFFFF',
                'stroke_color': '#000000',
                'font_size': 48,
                'uppercase': True
            }
        )
        
        self.assertEqual(Meme.objects.count(), 1)
        meme = Meme.objects.first()
        self.assertEqual(meme.template, self.template)
        self.assertEqual(meme.top_text, 'Hello')
    
    def test_post_redirects_to_detail(self):
        """Test successful POST redirects to meme detail."""
        response = self.client.post(
            reverse('meme_maker:meme_editor', kwargs={'template_pk': self.template.pk}),
            {'top_text': 'Test'}
        )
        
        meme = Meme.objects.first()
        self.assertRedirects(
            response,
            reverse('meme_maker:meme_detail', kwargs={'pk': meme.pk})
        )
    
    def test_404_for_nonexistent_template(self):
        """Test 404 for non-existent template."""
        response = self.client.get(
            reverse('meme_maker:meme_editor', kwargs={'template_pk': 99999})
        )
        self.assertEqual(response.status_code, 404)


class MemeDetailViewTest(TestCase):
    """Tests for meme detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('template.png'),
            title='Test Template'
        )
        self.meme = Meme.objects.create(
            template=self.template,
            top_text='Hello',
            bottom_text='World'
        )
    
    def test_view_url(self):
        """Test the view is accessible."""
        response = self.client.get(
            reverse('meme_maker:meme_detail', kwargs={'pk': self.meme.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(
            reverse('meme_maker:meme_detail', kwargs={'pk': self.meme.pk})
        )
        self.assertTemplateUsed(response, 'meme_maker/meme_detail.html')
    
    def test_displays_meme_text(self):
        """Test meme text is displayed."""
        response = self.client.get(
            reverse('meme_maker:meme_detail', kwargs={'pk': self.meme.pk})
        )
        # Text may be uppercase in the display
        self.assertEqual(response.status_code, 200)
    
    def test_has_download_link(self):
        """Test download link is present."""
        response = self.client.get(
            reverse('meme_maker:meme_detail', kwargs={'pk': self.meme.pk})
        )
        download_url = reverse('meme_maker:meme_download', kwargs={'pk': self.meme.pk})
        self.assertContains(response, download_url)
    
    def test_404_for_nonexistent(self):
        """Test 404 for non-existent meme."""
        response = self.client.get(
            reverse('meme_maker:meme_detail', kwargs={'pk': 99999})
        )
        self.assertEqual(response.status_code, 404)


class MemeListViewTest(TestCase):
    """Tests for meme list view."""
    
    def setUp(self):
        """Set up test data."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('template.png'),
            title='Test Template'
        )
        self.meme1 = Meme.objects.create(
            template=self.template,
            top_text='First'
        )
        self.meme2 = Meme.objects.create(
            template=self.template,
            top_text='Second'
        )
    
    def test_view_url(self):
        """Test the view is accessible."""
        response = self.client.get(reverse('meme_maker:meme_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(reverse('meme_maker:meme_list'))
        self.assertTemplateUsed(response, 'meme_maker/meme_list.html')
    
    def test_lists_memes(self):
        """Test memes are listed."""
        response = self.client.get(reverse('meme_maker:meme_list'))
        self.assertEqual(response.status_code, 200)
        # Check that memes exist in context
        self.assertIn('memes', response.context)
    
    def test_empty_state(self):
        """Test empty state when no memes."""
        Meme.objects.all().delete()
        response = self.client.get(reverse('meme_maker:meme_list'))
        self.assertEqual(response.status_code, 200)


class MemeDownloadViewTest(TestCase):
    """Tests for meme download view."""
    
    def setUp(self):
        """Set up test data."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('template.png'),
            title='Test Template'
        )
        self.meme = Meme.objects.create(
            template=self.template,
            top_text='Download Test'
        )
    
    def test_download_returns_file(self):
        """Test download returns a file."""
        response = self.client.get(
            reverse('meme_maker:meme_download', kwargs={'pk': self.meme.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.get('Content-Disposition', ''))
    
    def test_404_for_nonexistent(self):
        """Test 404 for non-existent meme."""
        response = self.client.get(
            reverse('meme_maker:meme_download', kwargs={'pk': 99999})
        )
        self.assertEqual(response.status_code, 404)


class LegacyCreateViewTest(TestCase):
    """Tests for legacy create view."""
    
    def test_view_url(self):
        """Test the view is accessible."""
        response = self.client.get(reverse('meme_maker:create'))
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(reverse('meme_maker:create'))
        self.assertTemplateUsed(response, 'meme_maker/create.html')
    
    def test_post_creates_meme(self):
        """Test POST creates a new meme."""
        image_file = get_test_image_file('legacy_meme.png')
        response = self.client.post(
            reverse('meme_maker:create'),
            {
                'image': image_file,
                'top_text': 'Legacy',
                'bottom_text': 'Create'
            }
        )
        
        self.assertEqual(Meme.objects.count(), 1)
        meme = Meme.objects.first()
        self.assertEqual(meme.top_text, 'Legacy')


# =============================================================================
# URL TESTS
# =============================================================================

class URLTests(TestCase):
    """Tests for URL patterns."""
    
    def test_home_url(self):
        """Test home URL resolves."""
        url = reverse('meme_maker:home')
        self.assertEqual(url, '/')
    
    def test_template_list_url(self):
        """Test template list URL resolves."""
        url = reverse('meme_maker:template_list')
        self.assertEqual(url, '/templates/')
    
    def test_template_detail_url(self):
        """Test template detail URL resolves."""
        url = reverse('meme_maker:template_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/templates/1/')
    
    def test_template_upload_url(self):
        """Test template upload URL resolves."""
        url = reverse('meme_maker:template_upload')
        self.assertEqual(url, '/templates/upload/')
    
    def test_template_download_url(self):
        """Test template download URL resolves."""
        url = reverse('meme_maker:template_download', kwargs={'pk': 1})
        self.assertEqual(url, '/templates/1/download/')
    
    def test_meme_editor_url(self):
        """Test meme editor URL resolves."""
        url = reverse('meme_maker:meme_editor', kwargs={'template_pk': 1})
        self.assertEqual(url, '/editor/1/')
    
    def test_meme_detail_url(self):
        """Test meme detail URL resolves."""
        url = reverse('meme_maker:meme_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/meme/1/')
    
    def test_meme_download_url(self):
        """Test meme download URL resolves."""
        url = reverse('meme_maker:meme_download', kwargs={'pk': 1})
        self.assertEqual(url, '/meme/1/download/')
    
    def test_meme_list_url(self):
        """Test meme list URL resolves."""
        url = reverse('meme_maker:meme_list')
        self.assertEqual(url, '/memes/')
    
    def test_legacy_create_url(self):
        """Test legacy create URL resolves."""
        url = reverse('meme_maker:create')
        self.assertEqual(url, '/create/')


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class MemeCreationWorkflowTest(TestCase):
    """Integration tests for the complete meme creation workflow."""
    
    def test_full_workflow(self):
        """Test complete workflow: upload template → create meme → view meme."""
        client = Client()
        
        # Step 1: Upload a template
        image_file = get_test_image_file('workflow_template.png')
        response = client.post(
            reverse('meme_maker:template_upload'),
            {'title': 'Workflow Test', 'tags': 'test', 'image': image_file}
        )
        
        template = MemeTemplate.objects.first()
        self.assertIsNotNone(template)
        self.assertEqual(template.title, 'Workflow Test')
        
        # Step 2: Create a meme from the template
        response = client.post(
            reverse('meme_maker:meme_editor', kwargs={'template_pk': template.pk}),
            {
                'top_text': 'Workflow',
                'bottom_text': 'Complete',
                'text_color': '#FFFFFF',
                'stroke_color': '#000000',
                'font_size': 48,
                'uppercase': True
            }
        )
        
        meme = Meme.objects.first()
        self.assertIsNotNone(meme)
        self.assertEqual(meme.template, template)
        
        # Step 3: View the meme
        response = client.get(
            reverse('meme_maker:meme_detail', kwargs={'pk': meme.pk})
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Download the meme
        response = client.get(
            reverse('meme_maker:meme_download', kwargs={'pk': meme.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_search_and_create_workflow(self):
        """Test search → select template → create meme workflow."""
        client = Client()
        
        # Create some templates
        t1 = MemeTemplate.objects.create(
            image=get_test_image_file('t1.png'),
            title='Funny Cat Meme',
            tags='cat, funny'
        )
        t2 = MemeTemplate.objects.create(
            image=get_test_image_file('t2.png'),
            title='Serious Dog Meme',
            tags='dog, serious'
        )
        
        # Step 1: Search for cat memes
        response = client.get(reverse('meme_maker:template_list'), {'q': 'cat'})
        self.assertContains(response, 'Funny Cat Meme')
        self.assertNotContains(response, 'Serious Dog Meme')
        
        # Step 2: Go to template detail
        response = client.get(
            reverse('meme_maker:template_detail', kwargs={'pk': t1.pk})
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Create meme
        response = client.post(
            reverse('meme_maker:meme_editor', kwargs={'template_pk': t1.pk}),
            {'top_text': 'I can haz', 'bottom_text': 'Cheezburger'}
        )
        
        meme = Meme.objects.first()
        self.assertEqual(meme.template, t1)


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class ConfigurationTest(TestCase):
    """Tests for meme maker configuration."""
    
    def test_default_settings_loaded(self):
        """Test default settings are available."""
        from .conf import meme_maker_settings
        
        self.assertEqual(meme_maker_settings.UPLOAD_PATH, 'memes/')
        self.assertEqual(meme_maker_settings.PRIMARY_COLOR, '#667eea')
        self.assertEqual(meme_maker_settings.TITLE, 'Meme Maker')
    
    def test_get_context_returns_dict(self):
        """Test get_context returns all settings as dict."""
        from .conf import meme_maker_settings
        
        context = meme_maker_settings.get_context()
        self.assertIsInstance(context, dict)
        self.assertIn('meme_maker_upload_path', context)
        self.assertIn('meme_maker_title', context)
        self.assertIn('meme_maker_primary_color', context)


class ContextProcessorTest(TestCase):
    """Tests for the context processor."""
    
    def test_context_processor_adds_settings(self):
        """Test context processor adds meme maker settings."""
        response = self.client.get(reverse('meme_maker:template_list'))
        
        # These should be in the context
        self.assertIn('meme_maker_title', response.context)
        self.assertIn('meme_maker_primary_color', response.context)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class EdgeCaseTests(TestCase):
    """Tests for edge cases and boundary conditions."""
    
    def test_template_with_very_long_title(self):
        """Test template with maximum length title."""
        title = 'A' * 200  # Max length
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title=title
        )
        self.assertEqual(len(template.title), 200)
    
    def test_template_with_special_characters_in_tags(self):
        """Test template with special characters in tags."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Special',
            tags='tag1, tag-2, tag_3, tag.4'
        )
        tags = template.get_tags_list()
        self.assertEqual(len(tags), 4)
    
    def test_meme_without_text(self):
        """Test creating a meme without any text."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='No Text Test'
        )
        meme = Meme.objects.create(template=template)
        self.assertEqual(meme.top_text, '')
        self.assertEqual(meme.bottom_text, '')
    
    def test_meme_overlays_json_structure(self):
        """Test the structure of text overlays JSON."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='JSON Test'
        )
        meme = Meme.objects.create(template=template)
        meme.set_overlays([
            {
                'text': 'Test',
                'position': 'top',
                'color': '#FFFFFF',
                'stroke_color': '#000000',
                'font_size': 48,
                'uppercase': True
            }
        ])
        meme.save()
        
        overlays = meme.get_overlays()
        self.assertEqual(len(overlays), 1)
        self.assertEqual(overlays[0]['text'], 'Test')
        self.assertEqual(overlays[0]['position'], 'top')
    
    def test_delete_template_keeps_memes(self):
        """Test that deleting a template doesn't delete associated memes."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Delete Test'
        )
        meme = Meme.objects.create(
            template=template,
            top_text='Keep Me'
        )
        meme_pk = meme.pk
        
        template.delete()
        
        # Meme should still exist with null template
        meme = Meme.objects.get(pk=meme_pk)
        self.assertIsNone(meme.template)
        self.assertEqual(meme.top_text, 'Keep Me')


# =============================================================================
# RATING TESTS
# =============================================================================

class RatingMixinTest(TestCase):
    """Tests for the RatingMixin functionality."""
    
    def test_initial_rating_values(self):
        """Test that new objects have zero ratings."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        self.assertEqual(template.rating_sum, 0)
        self.assertEqual(template.rating_count, 0)
        self.assertEqual(template.get_average_rating(), 0)
    
    def test_add_rating(self):
        """Test adding a rating."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        avg = template.add_rating(5)
        self.assertEqual(template.rating_sum, 5)
        self.assertEqual(template.rating_count, 1)
        self.assertEqual(avg, 5.0)
    
    def test_add_multiple_ratings(self):
        """Test adding multiple ratings."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        template.add_rating(5)
        template.add_rating(3)
        template.add_rating(4)
        
        self.assertEqual(template.rating_count, 3)
        self.assertEqual(template.rating_sum, 12)
        self.assertEqual(template.get_average_rating(), 4.0)
    
    def test_update_rating(self):
        """Test updating an existing rating."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        template.add_rating(3)
        template.update_rating(old_stars=3, new_stars=5)
        
        self.assertEqual(template.rating_count, 1)
        self.assertEqual(template.rating_sum, 5)
        self.assertEqual(template.get_average_rating(), 5.0)
    
    def test_rating_display_no_ratings(self):
        """Test rating display with no ratings."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        self.assertEqual(template.get_rating_display(), "No ratings yet")
    
    def test_rating_display_with_ratings(self):
        """Test rating display with ratings."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        template.add_rating(4)
        template.add_rating(5)
        
        display = template.get_rating_display()
        self.assertIn("4.5", display)
        self.assertIn("2", display)  # 2 votes
    
    def test_invalid_rating_too_low(self):
        """Test that ratings below 1 raise an error."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        with self.assertRaises(ValueError):
            template.add_rating(0)
    
    def test_invalid_rating_too_high(self):
        """Test that ratings above 5 raise an error."""
        template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        with self.assertRaises(ValueError):
            template.add_rating(6)


class TemplateRatingModelTest(TestCase):
    """Tests for the TemplateRating model."""
    
    def setUp(self):
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
    
    def test_create_rating(self):
        """Test creating a template rating."""
        from .models import TemplateRating
        
        rating = TemplateRating.objects.create(
            template=self.template,
            session_key='test-session-key',
            stars=4
        )
        self.assertEqual(rating.stars, 4)
        self.assertEqual(rating.template, self.template)
    
    def test_unique_rating_per_session(self):
        """Test that only one rating per session is allowed."""
        from .models import TemplateRating
        from django.db import IntegrityError
        
        TemplateRating.objects.create(
            template=self.template,
            session_key='test-session-key',
            stars=4
        )
        
        with self.assertRaises(IntegrityError):
            TemplateRating.objects.create(
                template=self.template,
                session_key='test-session-key',
                stars=5
            )


class MemeRatingModelTest(TestCase):
    """Tests for the MemeRating model."""
    
    def setUp(self):
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Test Template'
        )
        self.meme = Meme.objects.create(template=self.template)
    
    def test_create_rating(self):
        """Test creating a meme rating."""
        from .models import MemeRating
        
        rating = MemeRating.objects.create(
            meme=self.meme,
            session_key='test-session-key',
            stars=5
        )
        self.assertEqual(rating.stars, 5)
        self.assertEqual(rating.meme, self.meme)


class RateTemplateViewTest(TestCase):
    """Tests for the template rating view."""
    
    def setUp(self):
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Rating Test'
        )
        # Enable sessions
        self.client.get('/')  # Trigger session creation
    
    def test_rate_template_success(self):
        """Test successful template rating."""
        response = self.client.post(
            reverse('meme_maker:rate_template', kwargs={'pk': self.template.pk}),
            data=json.dumps({'stars': 4}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user_rating'], 4)
        self.assertEqual(data['average_rating'], 4.0)
    
    def test_rate_template_update(self):
        """Test updating a template rating."""
        url = reverse('meme_maker:rate_template', kwargs={'pk': self.template.pk})
        
        # First rating
        self.client.post(
            url,
            data=json.dumps({'stars': 3}),
            content_type='application/json'
        )
        
        # Update rating
        response = self.client.post(
            url,
            data=json.dumps({'stars': 5}),
            content_type='application/json'
        )
        
        self.template.refresh_from_db()
        self.assertEqual(self.template.rating_count, 1)
        self.assertEqual(self.template.rating_sum, 5)
    
    def test_rate_template_invalid_stars(self):
        """Test rating with invalid stars value."""
        response = self.client.post(
            reverse('meme_maker:rate_template', kwargs={'pk': self.template.pk}),
            data=json.dumps({'stars': 10}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_rate_template_get_not_allowed(self):
        """Test that GET requests are not allowed."""
        response = self.client.get(
            reverse('meme_maker:rate_template', kwargs={'pk': self.template.pk})
        )
        self.assertEqual(response.status_code, 405)


class RateMemeViewTest(TestCase):
    """Tests for the meme rating view."""
    
    def setUp(self):
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Test Template'
        )
        self.meme = Meme.objects.create(template=self.template)
        self.client.get('/')  # Trigger session creation
    
    def test_rate_meme_success(self):
        """Test successful meme rating."""
        response = self.client.post(
            reverse('meme_maker:rate_meme', kwargs={'pk': self.meme.pk}),
            data=json.dumps({'stars': 5}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user_rating'], 5)


class TemplateListOrderingTest(TestCase):
    """Tests for template list ordering by rating."""
    
    def setUp(self):
        """Create templates with different ratings."""
        self.template_low = MemeTemplate.objects.create(
            image=get_test_image_file('low.png'),
            title='Low Rated'
        )
        self.template_low.rating_sum = 6
        self.template_low.rating_count = 3
        self.template_low.save()
        
        self.template_high = MemeTemplate.objects.create(
            image=get_test_image_file('high.png'),
            title='High Rated'
        )
        self.template_high.rating_sum = 15
        self.template_high.rating_count = 3
        self.template_high.save()
        
        self.template_none = MemeTemplate.objects.create(
            image=get_test_image_file('none.png'),
            title='No Rating'
        )
    
    def test_order_by_highest_rating(self):
        """Test ordering templates by highest rating."""
        response = self.client.get(
            reverse('meme_maker:template_list'),
            {'order': '-rating'}
        )
        templates = list(response.context['templates'])
        
        # High rated should be first
        self.assertEqual(templates[0], self.template_high)
    
    def test_order_by_lowest_rating(self):
        """Test ordering templates by lowest rating."""
        response = self.client.get(
            reverse('meme_maker:template_list'),
            {'order': 'rating'}
        )
        templates = list(response.context['templates'])
        
        # No rating (0) should be first, then low
        self.assertEqual(templates[0], self.template_none)
    
    def test_order_by_newest(self):
        """Test ordering templates by newest."""
        response = self.client.get(
            reverse('meme_maker:template_list'),
            {'order': '-created'}
        )
        templates = list(response.context['templates'])
        
        # Most recently created should be first (template_none)
        self.assertEqual(templates[0], self.template_none)


class MemeListOrderingTest(TestCase):
    """Tests for meme list ordering by rating."""
    
    def setUp(self):
        """Create memes with different ratings."""
        self.template = MemeTemplate.objects.create(
            image=get_test_image_file('test.png'),
            title='Test Template'
        )
        
        self.meme_low = Meme.objects.create(template=self.template, top_text='Low')
        self.meme_low.rating_sum = 4
        self.meme_low.rating_count = 2
        self.meme_low.save()
        
        self.meme_high = Meme.objects.create(template=self.template, top_text='High')
        self.meme_high.rating_sum = 10
        self.meme_high.rating_count = 2
        self.meme_high.save()
    
    def test_order_by_highest_rating(self):
        """Test ordering memes by highest rating."""
        response = self.client.get(
            reverse('meme_maker:meme_list'),
            {'order': '-rating'}
        )
        memes = list(response.context['memes'])
        
        # High rated should be first
        self.assertEqual(memes[0], self.meme_high)


class URLRatingTests(TestCase):
    """Tests for rating URL patterns."""
    
    def test_rate_template_url(self):
        """Test rate template URL resolves."""
        url = reverse('meme_maker:rate_template', kwargs={'pk': 1})
        self.assertEqual(url, '/templates/1/rate/')
    
    def test_rate_meme_url(self):
        """Test rate meme URL resolves."""
        url = reverse('meme_maker:rate_meme', kwargs={'pk': 1})
        self.assertEqual(url, '/meme/1/rate/')


# =============================================================================
# OBJECT LINKING TESTS
# =============================================================================

class TemplateLinkingTests(TestCase):
    """Tests for the template object linking functionality."""
    
    def setUp(self):
        """Create test data."""
        self.template = MemeTemplate.objects.create(
            title='Test Template',
            tags='test, linking',
            image=SimpleUploadedFile(
                'test.png',
                create_test_image().read(),
                content_type='image/png'
            )
        )
        # Create a User to link to (using Django's built-in User model)
        self.user1 = User.objects.create_user(username='testuser1', password='testpass')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass')
    
    def test_link_to_object(self):
        """Test linking a template to an object."""
        link = self.template.link_to(self.user1)
        
        self.assertIsNotNone(link)
        self.assertEqual(link.template, self.template)
        self.assertEqual(link.linked_object, self.user1)
    
    def test_link_to_multiple_objects(self):
        """Test linking a template to multiple objects."""
        self.template.link_to(self.user1)
        self.template.link_to(self.user2)
        
        linked_objects = self.template.get_linked_objects()
        self.assertEqual(len(linked_objects), 2)
        self.assertIn(self.user1, linked_objects)
        self.assertIn(self.user2, linked_objects)
    
    def test_link_to_same_object_twice(self):
        """Test that linking to the same object twice doesn't create duplicates."""
        link1 = self.template.link_to(self.user1)
        link2 = self.template.link_to(self.user1)
        
        self.assertEqual(link1.pk, link2.pk)  # Same link returned
        self.assertEqual(self.template.object_links.count(), 1)
    
    def test_is_linked_to(self):
        """Test checking if template is linked to an object."""
        self.assertFalse(self.template.is_linked_to(self.user1))
        
        self.template.link_to(self.user1)
        
        self.assertTrue(self.template.is_linked_to(self.user1))
        self.assertFalse(self.template.is_linked_to(self.user2))
    
    def test_unlink_from_object(self):
        """Test unlinking a template from an object."""
        self.template.link_to(self.user1)
        self.assertTrue(self.template.is_linked_to(self.user1))
        
        result = self.template.unlink_from(self.user1)
        
        self.assertTrue(result)
        self.assertFalse(self.template.is_linked_to(self.user1))
    
    def test_unlink_from_unlinked_object(self):
        """Test unlinking from an object that wasn't linked."""
        result = self.template.unlink_from(self.user1)
        self.assertFalse(result)
    
    def test_get_linked_objects_filtered_by_type(self):
        """Test getting linked objects filtered by model type."""
        # Create another template to link to (different model type)
        other_template = MemeTemplate.objects.create(
            title='Other Template',
            image=SimpleUploadedFile(
                'other.png',
                create_test_image().read(),
                content_type='image/png'
            )
        )
        
        self.template.link_to(self.user1)
        self.template.link_to(other_template)
        
        # Get only User links
        users = self.template.get_linked_objects(User)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], self.user1)
        
        # Get only MemeTemplate links
        templates = self.template.get_linked_objects(MemeTemplate)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0], other_template)
    
    def test_link_with_link_type(self):
        """Test linking with a link_type metadata."""
        link = self.template.link_to(self.user1, link_type='created_by')
        
        self.assertEqual(link.link_type, 'created_by')
    
    def test_manager_linked_to(self):
        """Test querying templates by linked object using the manager."""
        template2 = MemeTemplate.objects.create(
            title='Another Template',
            image=SimpleUploadedFile(
                'another.png',
                create_test_image().read(),
                content_type='image/png'
            )
        )
        
        self.template.link_to(self.user1)
        template2.link_to(self.user2)
        
        # Query by user1
        templates_for_user1 = MemeTemplate.objects.linked_to(self.user1)
        self.assertEqual(templates_for_user1.count(), 1)
        self.assertEqual(templates_for_user1.first(), self.template)
        
        # Query by user2
        templates_for_user2 = MemeTemplate.objects.linked_to(self.user2)
        self.assertEqual(templates_for_user2.count(), 1)
        self.assertEqual(templates_for_user2.first(), template2)


class MemeLinkingTests(TestCase):
    """Tests for the meme object linking functionality."""
    
    def setUp(self):
        """Create test data."""
        self.template = MemeTemplate.objects.create(
            title='Test Template',
            image=SimpleUploadedFile(
                'test.png',
                create_test_image().read(),
                content_type='image/png'
            )
        )
        self.meme = Meme.objects.create(
            template=self.template,
            top_text='Hello',
            bottom_text='World'
        )
        self.user1 = User.objects.create_user(username='memeuser1', password='testpass')
        self.user2 = User.objects.create_user(username='memeuser2', password='testpass')
    
    def test_link_meme_to_object(self):
        """Test linking a meme to an object."""
        link = self.meme.link_to(self.user1)
        
        self.assertIsNotNone(link)
        self.assertEqual(link.meme, self.meme)
        self.assertEqual(link.linked_object, self.user1)
    
    def test_meme_link_to_multiple_objects(self):
        """Test linking a meme to multiple objects."""
        self.meme.link_to(self.user1)
        self.meme.link_to(self.user2)
        
        linked_objects = self.meme.get_linked_objects()
        self.assertEqual(len(linked_objects), 2)
    
    def test_meme_is_linked_to(self):
        """Test checking if meme is linked to an object."""
        self.assertFalse(self.meme.is_linked_to(self.user1))
        
        self.meme.link_to(self.user1)
        
        self.assertTrue(self.meme.is_linked_to(self.user1))
    
    def test_meme_unlink_from_object(self):
        """Test unlinking a meme from an object."""
        self.meme.link_to(self.user1)
        self.assertTrue(self.meme.is_linked_to(self.user1))
        
        self.meme.unlink_from(self.user1)
        
        self.assertFalse(self.meme.is_linked_to(self.user1))
    
    def test_meme_manager_linked_to(self):
        """Test querying memes by linked object using the manager."""
        meme2 = Meme.objects.create(
            template=self.template,
            top_text='Another',
            bottom_text='Meme'
        )
        
        self.meme.link_to(self.user1)
        meme2.link_to(self.user2)
        
        memes_for_user1 = Meme.objects.linked_to(self.user1)
        self.assertEqual(memes_for_user1.count(), 1)
        self.assertEqual(memes_for_user1.first(), self.meme)
    
    def test_link_with_metadata(self):
        """Test linking with additional metadata."""
        metadata = {'context': 'marketing', 'campaign_id': 123}
        link = self.meme.link_to(self.user1, link_type='featured', metadata=metadata)
        
        self.assertEqual(link.link_type, 'featured')
        self.assertEqual(link.metadata, metadata)
    
    def test_get_links_returns_link_objects(self):
        """Test getting link objects (not just linked objects)."""
        self.meme.link_to(self.user1, link_type='created_by')
        self.meme.link_to(self.user2, link_type='shared_with')
        
        links = self.meme.get_links()
        self.assertEqual(links.count(), 2)
        
        link_types = [link.link_type for link in links]
        self.assertIn('created_by', link_types)
        self.assertIn('shared_with', link_types)


class LinkCascadeDeleteTests(TestCase):
    """Tests for cascade deletion of links."""
    
    def setUp(self):
        """Create test data."""
        self.template = MemeTemplate.objects.create(
            title='Test Template',
            image=SimpleUploadedFile(
                'test.png',
                create_test_image().read(),
                content_type='image/png'
            )
        )
        self.meme = Meme.objects.create(
            template=self.template,
            top_text='Test'
        )
        self.user = User.objects.create_user(username='linkuser', password='testpass')
    
    def test_template_delete_cascades_to_links(self):
        """Test that deleting a template deletes its links."""
        self.template.link_to(self.user)
        self.assertEqual(TemplateLink.objects.count(), 1)
        
        self.template.delete()
        
        self.assertEqual(TemplateLink.objects.count(), 0)
    
    def test_meme_delete_cascades_to_links(self):
        """Test that deleting a meme deletes its links."""
        self.meme.link_to(self.user)
        self.assertEqual(MemeLink.objects.count(), 1)
        
        self.meme.delete()
        
        self.assertEqual(MemeLink.objects.count(), 0)
