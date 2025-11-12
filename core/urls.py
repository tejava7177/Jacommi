# core/urls.py
from django.urls import path
from .views import (
    today_page, health, mypage,
    fcm_register, fcm_unregister,
    api_sentence_save, api_sentence_delete,
)
from .views_auth import google_login, google_callback
from .api import calendar_insert_today

urlpatterns = [
    path("", today_page, name="today"),
    path("health", health, name="health"),
    path("mypage", mypage, name="mypage"),

    path("api/auth/google/login", google_login, name="google_login"),
    path("api/auth/google/callback", google_callback, name="google_callback"),

    path("api/sentences/save", api_sentence_save, name="api_sentence_save"),
    # ✅ 경로 파라미터로 통일(끝에 슬래시 포함)
    path("api/sentences/delete/<int:sentence_id>/", api_sentence_delete, name="api_sentence_delete"),

    path("api/fcm/register", fcm_register, name="api_fcm_register"),
    path("api/fcm/unregister", fcm_unregister, name="api_fcm_unregister"),

    path("api/calendar/insert-today", calendar_insert_today, name="api_calendar_insert_today"),
]