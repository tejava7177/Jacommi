# core/metrics.py
from prometheus_client import Counter, Histogram

# HTTP 요청 카운트
HTTP_REQUESTS_TOTAL = Counter(
    "jacommi_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

# 요청 처리 시간
HTTP_REQUEST_LATENCY_SECONDS = Histogram(
    "jacommi_http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["path"],
)