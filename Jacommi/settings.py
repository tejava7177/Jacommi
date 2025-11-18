"""
Django settings for Jacommi project (minimal dev setup).
"""
from pathlib import Path
import os


# --- Security / Debug (dev defaults) ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")  # ⚠️ set env in production
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

# CSRF: allow local dev + Docker (8000/8001)
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
    "http://localhost:8000",
    "http://localhost:8001",
]

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False




BASE_DIR = Path(__file__).resolve().parent.parent

# --- Static files ---
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



# --- Applications ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    # Local apps
    "core",  # ← 생성 후 주석 해제
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Jacommi.urls"

# --- Templates ---
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

# --- Database ---

# DB_HOST 환경변수가 있으면 Postgres, 없으면 sqlite3 사용
if os.getenv("DB_HOST"):
    # Docker / 배포 환경: Postgres
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "jacommi"),
            "USER": os.getenv("DB_USER", "jacommi"),
            "PASSWORD": os.getenv("DB_PASSWORD", "jacommi-password"),
            "HOST": os.getenv("DB_HOST", "db"),   # docker-compose 서비스 이름
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


# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# --- Default primary key ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
