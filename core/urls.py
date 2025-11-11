from django.urls import path
from .views import today_page, health, fcm_register, fcm_unregister
from .views_auth import google_login, google_callback
from .api import calendar_insert_today  # ← api.py에 구현

urlpatterns = [
    # 웹페이지
    path("", today_page, name="today"),
    path("health", health, name="health"),

    # Google OAuth
    path("api/auth/google/login", google_login, name="google_login"),
    path("api/auth/google/callback", google_callback, name="google_callback"),

    # FCM 토큰 등록/해제
    path("api/fcm/register", fcm_register, name="api_fcm_register"),
    path("api/fcm/unregister", fcm_unregister, name="api_fcm_unregister"),

    # 오늘 문장 캘린더에 저장
    path("api/calendar/insert-today", calendar_insert_today, name="api_calendar_insert_today"),
]