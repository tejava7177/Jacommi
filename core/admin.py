from django.contrib import admin
from .models import DailySet, ApiUsageLog


@admin.register(DailySet)
class DailySetAdmin(admin.ModelAdmin):
    list_display = ("date", "topic", "created_at")
    search_fields = ("topic",)
    ordering = ("-date",)


@admin.register(ApiUsageLog)
class ApiUsageLogAdmin(admin.ModelAdmin):
    list_display = ("date", "model", "prompt_tokens", "completion_tokens", "total_tokens", "cost_usd", "created_at")
    list_filter = ("model", "date")
    ordering = ("-created_at",)