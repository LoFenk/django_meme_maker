from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('meme_maker', '0007_remove_legacy_meme_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='memetemplate',
            name='flagged',
            field=models.BooleanField(default=False, help_text='Flagged for review'),
        ),
        migrations.AddField(
            model_name='memetemplate',
            name='flagged_at',
            field=models.DateTimeField(blank=True, help_text='When this template was flagged', null=True),
        ),
        migrations.AddField(
            model_name='meme',
            name='flagged',
            field=models.BooleanField(default=False, help_text='Flagged for review'),
        ),
        migrations.AddField(
            model_name='meme',
            name='flagged_at',
            field=models.DateTimeField(blank=True, help_text='When this meme was flagged', null=True),
        ),
        migrations.CreateModel(
            name='TemplateFlag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flags', to='meme_maker.memetemplate')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_flags', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('template', 'user')},
            },
        ),
        migrations.CreateModel(
            name='MemeFlag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flags', to='meme_maker.meme')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meme_flags', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('meme', 'user')},
            },
        ),
        migrations.AddIndex(
            model_name='templateflag',
            index=models.Index(fields=['created_at'], name='meme_maker_templateflag_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='memeflag',
            index=models.Index(fields=['created_at'], name='meme_maker_memeflag_created_at_idx'),
        ),
    ]
