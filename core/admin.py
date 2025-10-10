from django.contrib import admin
from .models import DailySet, ApiUsageLog
from .models import FcmToken
from .models import GoogleAccount

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


@admin.register(FcmToken)
class FcmTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "platform", "active", "created_at")
    search_fields = ("token",)
    list_filter = ("platform", "active")


@admin.register(GoogleAccount)
class GoogleAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "calendar_id", "last_event_date")
    search_fields = ("email",)