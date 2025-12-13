from django.contrib import admin
from .models import Meme

@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = ['id', 'top_text', 'bottom_text', 'created_at']
    list_filter = ['created_at']
    search_fields = ['top_text', 'bottom_text']
    readonly_fields = ['created_at']
