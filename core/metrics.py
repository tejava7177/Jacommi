# core/metrics.py
from prometheus_client import Counter, Histogram

# =========================
# 1) HTTP 레벨 메트릭
# =========================

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

# =========================
# 2) 비즈니스 메트릭
# =========================

# 1) DailySet 생성 결과
# result 라벨: success / fallback / error 등으로 쓰면 됨
DAILYSET_EVENTS_TOTAL = Counter(
    "jacommi_dailyset_events_total",
    "DailySet generation events",
    ["result"],  # e.g. "success", "fallback", "error"
)

# 2) OpenAI 호출 횟수
# outcome 라벨: success / error
OPENAI_REQUESTS_TOTAL = Counter(
    "jacommi_openai_requests_total",
    "OpenAI chat completion requests",
    ["model", "outcome"],  # e.g. model="gpt-4o-mini", outcome="success"
)

# 3) OpenAI 토큰 사용량
# kind 라벨: prompt / completion / total
OPENAI_TOKENS_TOTAL = Counter(
    "jacommi_openai_tokens_total",
    "Tokens used for OpenAI calls",
    ["model", "kind"],  # kind="prompt" | "completion" | "total"
)

# 4) FCM 푸시 이벤트
# kind: daily / test 등, result: success / error
FCM_PUSH_EVENTS_TOTAL = Counter(
    "jacommi_fcm_push_events_total",
    "FCM push notifications sent",
    ["kind", "result"],  # kind="daily"|"test", result="success"|"error"
)

# 5) 문장/캘린더 저장 이벤트
# action: sentence_save / calendar_insert
SAVING_EVENTS_TOTAL = Counter(
    "jacommi_saving_events_total",
    "Sentence & calendar saving events",
    ["action", "result"],  # action="sentence_save"|"calendar_insert", result="success"|"error"
)