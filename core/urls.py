from django.urls import path
from .views import today_page, health
from .views_auth import google_login, google_callback

urlpatterns = [
    # 웹페이지
    path("", today_page, name="today"),
    path("health", health, name="health"),

    # Google OAuth
    path("api/auth/google/login", google_login, name="google_login"),
    path("api/auth/google/callback", google_callback, name="google_callback"),
]