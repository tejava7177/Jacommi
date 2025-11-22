# core/middleware.py
import time
import socket
import os

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

        # HTTP 요청 수 / 지연시간 기록
        HTTP_REQUEST_LATENCY_SECONDS.labels(path=path).observe(duration)
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            path=path,
            status=response.status_code,
        ).inc()

        return response


class ServerIdHeaderMiddleware:
    """
    각 응답에 X-Server-ID 헤더를 추가하는 미들웨어.
    로드밸런서 뒤쪽에서 어떤 인스턴스가 응답했는지 확인할 수 있다.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # 기본값: 호스트 이름(컨테이너/EC2 이름)
        self.hostname = socket.gethostname()
        # 필요하면 EC2 Instance ID를 env로 주입해도 됨
        self.instance_id = os.environ.get("EC2_INSTANCE_ID", self.hostname)

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Server-ID"] = self.instance_id
        return response