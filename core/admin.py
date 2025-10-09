from django.contrib import admin
from .models import DailySet

@admin.register(DailySet)
class DailySetAdmin(admin.ModelAdmin):
    list_display = ("date", "topic", "created_at")
    search_fields = ("topic",)
    ordering = ("-date",)