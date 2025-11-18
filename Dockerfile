# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 시스템 의존성(필요 시 추가)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# Django 설정 모듈
ENV DJANGO_SETTINGS_MODULE=Jacommi.settings

# 정적 파일 수집 (STATIC_ROOT로)
RUN python manage.py collectstatic --noinput

# Gunicorn으로 서비스 실행
CMD ["gunicorn", "Jacommi.wsgi:application", "--bind", "0.0.0.0:8000"]