from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meme_maker', '0006_add_nsfw_flags'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='meme',
            name='image',
        ),
        migrations.RemoveField(
            model_name='meme',
            name='top_text',
        ),
        migrations.RemoveField(
            model_name='meme',
            name='bottom_text',
        ),
    ]
