# core/views_metrics.py
from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


def metrics_view(request):
    # 인증 없이 노출해도 되는지 판단은 주흔이 선택,
    # 지금은 편의상 누구나 볼 수 있게 둔다.
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)