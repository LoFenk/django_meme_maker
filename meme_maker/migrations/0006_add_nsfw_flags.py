from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meme_maker', '0005_add_object_linking'),
    ]

    operations = [
        migrations.AddField(
            model_name='memetemplate',
            name='nsfw',
            field=models.BooleanField(default=False, help_text='Mark this template as not safe for work'),
        ),
        migrations.AddField(
            model_name='meme',
            name='nsfw',
            field=models.BooleanField(default=False, help_text='Mark this meme as not safe for work'),
        ),
    ]
