from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meme_maker', '0009_rename_meme_maker_memeflag_created_at_idx_meme_maker__created_e695fa_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalSourceQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(choices=[('imgflip', 'Imgflip')], max_length=50)),
                ('query_str', models.CharField(help_text='Original query string', max_length=300)),
                ('normalized_query', models.CharField(db_index=True, help_text='Normalized query for cache lookups', max_length=300)),
                ('fetched_at', models.DateTimeField(blank=True, help_text='When this query was last fetched from the external source', null=True)),
                ('result_json', models.JSONField(blank=True, default=dict, help_text='Raw API response payload')),
                ('status', models.CharField(choices=[('success', 'Success'), ('error', 'Error')], default='error', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('site_name', 'normalized_query'), name='unique_external_query')],
                'indexes': [models.Index(fields=['fetched_at'], name='meme_maker__fetched_at_idx')],
            },
        ),
    ]
