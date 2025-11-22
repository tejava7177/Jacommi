"""
Django settings for Jacommi project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================
# 1. Security / Debug
# ==========================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

# ex) DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,web,3.34.98.58,jacommi.store,www.jacommi.store
ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost",
).split(",")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS if h.strip()]

# CSRF: 로컬 + Docker + 실제 도메인(jacommi.store)
CSRF_TRUSTED_ORIGINS = [
    # 로컬/도커 개발용
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
    "http://localhost:8000",
    "http://localhost:8001",
    # 실제 서비스 도메인 (nginx + certbot 로 HTTPS 종단)
    "https://jacommi.store",
    "https://www.jacommi.store",
]

# HTTPS 관련 옵션은 DEBUG 여부에 따라 분기
if DEBUG:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
else:
    # 배포 환경: 항상 HTTPS 로 접근한다고 가정
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False
    # Nginx 에서 넘겨준 X-Forwarded-Proto 로 HTTPS 여부 판단
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")




# ==========================
# 2. Static files
# ==========================

STATIC_URL = "/static/"

# 개발용: 프로젝트 안의 static 디렉터리
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# 배포용: collectstatic 이 모아줄 디렉터리
STATIC_ROOT = BASE_DIR / "staticfiles"

# DEBUG=False 에서 WhiteNoise가 이 스토리지를 사용해 압축/해시 버전 제공
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==========================
# 3. Applications
# ==========================

INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    # Local apps
    "core",
]

# ==========================
# 4. Middleware
# ==========================

MIDDLEWARE = [
    # ✅ Prometheus: request 처리 전에 계측
    "django_prometheus.middleware.PrometheusBeforeMiddleware",

    # Django 기본 미들웨어들
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # ✅ 우리 커스텀 메트릭/헤더 미들웨어
    "core.middleware.PrometheusRequestMiddleware",
    "core.middleware.ServerIdHeaderMiddleware",

    # ✅ Prometheus: response 후 마무리 계측
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "Jacommi.urls"

# ==========================
# 5. Templates
# ==========================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Jacommi.wsgi.application"

# ==========================
# 6. Database
# ==========================

# DB_HOST 환경변수가 있으면 Postgres, 없으면 sqlite3 사용
if os.getenv("DB_HOST"):
    # Django + Prometheus용 Postgres 백엔드
    DATABASES = {
        "default": {
            "ENGINE": "django_prometheus.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "jacommi"),
            "USER": os.getenv("DB_USER", "jacommi"),
            "PASSWORD": os.getenv("DB_PASSWORD", "jacommi-password"),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    # 로컬 개발용: sqlite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ==========================
# 7. Auth / I18N / etc.
# ==========================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"