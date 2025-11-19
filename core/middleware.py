# core/middleware.py
import time
from .metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_LATENCY_SECONDS


class PrometheusRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        method = request.method

        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start

        # 단순하게 path 그대로 라벨에 넣지만,
        # 나중에 /api/something/<id>/ 같은 건 패턴으로 정규화해도 됨
        HTTP_REQUEST_LATENCY_SECONDS.labels(path=path).observe(duration)
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            path=path,
            status=response.status_code,
        ).inc()

        return response