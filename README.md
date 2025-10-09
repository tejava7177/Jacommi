# Jacommi
프로젝트 컨텍스트(문맥) 정의

1) 한 줄 요약

하루 1회(자정) GPT API로 비즈니스 일본어 회화 5문장을 생성·저장하고, 모든 사용자에게 동일한 오늘의 문장을 제공하는 웹서비스. PWA + FCM으로 09:00~20:00 매시간 알림, Google 로그인으로 캘린더 자동 기록, 웹 읽어주기(TTS), 보안/요금 모니터링까지 포함.

⸻

2) GPT와의 협업 원칙 (Context Engineering)
	•	목표 정렬: “일본 IT 기업 현업에서 쓰는 자연스러운 회화표현 5문장/일” 고정.
	•	응답 스타일: 설계/코드/프로세스는 구체적이고 실행 가능한 형태로. 설명은 간결 + 체크리스트 지향.
	•	결정 방식: 모호하면 합리적 기본값을 제안하고 바로 설계까지 작성. (예: 타임존 Asia/Seoul, 생성 시간 00:00, 알림 9~20시 매시)
	•	개발 인도: 1) 기능 쪼개기 → 2) 데이터모델 → 3) API 계약 → 4) 배치/작업자 → 5) 프런트 연동 → 6) 모니터링 순으로 PR 만들 수 있는 단위로 분리.
	•	품질 가드: 출력 스키마 강제(JSON), 예시·테스트 프롬프트 제공, 금칙어/스타일 규칙 포함.
	•	보안/비용: 서버사이드에서만 GPT 호출, 키는 비밀관리, 토큰 로깅/예산 알림.

⸻

3) 사용자 스토리
	1.	유저는 웹에 접속해 오늘의 5문장을 본다(모두 동일).
	2.	PWA 설치 후 09~20시 매시 정각에 푸시로 5문장 카드(혹은 하나씩 시차 발송).
	3.	Google 로그인 시 내 캘린더에 “오늘의 학습표현” 이벤트가 매일 생성(요약+본문은 5문장).
	4.	문장 카드에서 재생 버튼으로 웹 스피치 TTS로 일본어 음성 청취.

⸻

4) 생성 컨텐츠 규격 (출력 스키마)
	•	요구사항: 비즈니스/IT 현업 문장, 각 문장 평문, 한자에 히라가나( ) 병기, 한국어 해석. 예)
	•	jp: 今日(きょう)のスプリント計画(けいかく)について共有(きょうゆう)します。
	•	ko: 오늘 스프린트 계획에 대해 공유하겠습니다.
	•	JSON 스키마 (하루 세트):

{
  "date": "YYYY-MM-DD",
  "topic": "스프린트 계획共有",
  "sentences": [
    {"jp": "...", "ko": "..."},
    {"jp": "...", "ko": "..."},
    {"jp": "...", "ko": "..."},
    {"jp": "...", "ko": "..."},
    {"jp": "...", "ko": "..."}
  ],
  "meta": {"level": "B1-B2", "tags": ["회의", "개발", "리뷰"]}
}

	•	스타일 가이드
	•	톤: 정중체(です/ます調). 길이: 문장당 12~25자 내외.
	•	금칙: 지나친 문학적 표현, 학습자에게 난해한 고유명사 남발 금지.
	•	도메인: 스프린트/티켓/릴리즈/장애/코드리뷰/요건정의/견적/일정조정 등.

⸻

5) 프롬프트 설계

System

당신은 일본 IT 기업 현업 PM 겸 일본어 교육 전문가입니다. 학습자(한국어권)에게 비즈니스 일본어 회화 5문장을 생성합니다. 각 문장은 한자에 히라가나를 괄호로 병기하고, 간결한 한국어 번역을 제공합니다. 톤은 정중하고 업무 맥락에 맞게 자연스러워야 합니다. 출력은 지정한 JSON 스키마로만 반환하세요. 불필요한 설명을 포함하지 마세요.

User(예시)

오늘 날짜는 2025-10-09, 주제는 "스프린트 계획 회의". 난이도 B1-B2.
형식: {date, topic, sentences[ {jp, ko} x5 ], meta{ level, tags[] }} 로만 출력.

베리데이션 규칙
	•	반환 JSON 파싱 실패 시 재시도.
	•	문장 수 5개 강제, jp/ko 필드 누락 시 재생성.

⸻

6) 아키텍처 개요
	•	백엔드: Django (REST Framework)
	•	배치/스케줄러: Celery Beat 또는 Django-crontab (00:00 KST, 09~20시 매시 푸시)
	•	DB: Postgres (문장 세트/로그/사용자/알림토큰/캘린더 상태)
	•	외부: OpenAI API, Firebase Cloud Messaging, Google OAuth2 + Calendar API
	•	프런트: PWA(React 또는 Django Template + Service Worker), Web Speech API(TTS)

⸻

7) 데이터 모델(초안)

# models.py
from django.db import models
from django.contrib.auth.models import User

class DailySet(models.Model):
    date = models.DateField(unique=True)
    topic = models.CharField(max_length=100)
    payload = models.JSONField()  # 스키마 그대로 저장
    created_at = models.DateTimeField(auto_now_add=True)

class FcmToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=300, unique=True)
    platform = models.CharField(max_length=20, default="web")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ApiUsageLog(models.Model):
    date = models.DateField()
    model = models.CharField(max_length=50)
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    cost_usd = models.DecimalField(max_digits=8, decimal_places=4)
    meta = models.JSONField(default=dict)

class GoogleAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    refresh_token = models.TextField()
    email = models.EmailField()
    calendar_id = models.CharField(max_length=200, default='primary')
    last_event_date = models.DateField(null=True, blank=True)


⸻

8) API 설계 (REST)
	•	GET /api/today → 오늘 세트 반환(JSON)
	•	POST /api/fcm/register → {token} 저장/갱신
	•	POST /api/push/now (admin) → 즉시 브로드캐스트
	•	GET /api/usage (admin) → 요금/토큰 요약
	•	GET /api/auth/google/login → OAuth 시작
	•	GET /api/auth/google/callback → 토큰 저장

응답 예시:

GET /api/today -> 200
{ "date":"2025-10-09", "topic":"스프린트計画", "sentences":[...], "meta":{...} }


⸻

9) 배치 파이프라인
	1.	00:00 generate_daily_set()
	•	이미 존재하면 skip.
	•	OpenAI 호출 → JSON 검증 → DB 저장 → 관리용 Slack/Webhook 알림.
	2.	09:00~20:00 매시 broadcast_today_set()
	•	FCM topic(all) or 토큰 리스트로 푸시 발송.
	•	iOS 사파리 제약 고려(대안: 로컬 알람 UI 안내).
	3.	캘린더 기록
	•	Google 연결된 유저에 대해 해당 날짜 이벤트 upsert (중복 방지: externalId/summary+date 키).

⸻

10) OpenAI 호출 예시 (서버사이드)

import os, json
from openai import OpenAI
from django.utils import timezone

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_messages(date_str, topic):
    system = """당신은 일본 IT 기업 현업 PM 겸 일본어 교육 전문가입니다... JSON만 반환"""
    user = f"오늘 날짜는 {date_str}, 주제는 '{topic}'. 난이도 B1-B2. 형식은 {...}"
    return [{"role":"system","content":system},{"role":"user","content":user}]


def generate_daily_set(topic="스프린트 계획 회의"):
    date_str = timezone.localdate().isoformat()
    msgs = build_messages(date_str, topic)
    resp = client.chat.completions.create(
        model="gpt-5.1-mini",
        messages=msgs,
        temperature=0.7,
        response_format={"type":"json_object"}
    )
    data = json.loads(resp.choices[0].message.content)
    # validate count == 5, fields exist
    assert len(data.get("sentences", [])) == 5
    return data, resp.usage


⸻

11) 비용 모니터링
	•	저장: ApiUsageLog에 일별 합계 저장(프롬프트/완료 토큰, USD).
	•	계산: 모델별 단가 테이블(환경변수/설정).
	•	알림: 일일 1$ 초과/월간 20$ 초과 시 Slack/Webhook.

⸻

12) FCM & PWA 개요
	•	PWA: manifest.json(name, icons, start_url, display=standalone), service-worker.js(push 이벤트 핸들러, 캐싱 전략).
	•	FCM: 웹 키 세팅, 토픽 구독(all), 서버에서 message:{ notification:title/body, data:json } 발송.
	•	푸시 페이로드 예:

{
  "topic": "all",
  "notification": {"title": "오늘의 일본어 5문장", "body": "스프린트計画: 5문장 확인"},
  "data": {"date":"2025-10-09"}
}

	•	클라이언트 처리: 알림 클릭 → /today 오픈.

⸻

13) 웹 음성 (TTS)
	•	1차: Web Speech API (크롬/엣지 안정). 일본어 voice 선택 우선.
	•	2차 옵션: Google Cloud TTS/Azure TTS로 품질 향상(서버서명 URL로 오디오 제공).
	•	프런트 유틸

export function speakJa(text){
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'ja-JP';
  window.speechSynthesis.speak(u);
}


⸻

14) Google 로그인 & 캘린더
	•	OAuth 범위: openid email profile, https://www.googleapis.com/auth/calendar.
	•	플로우: 로그인 → refresh_token 저장 → 배치에서 events.insert(idempotent: same date summary 체크).
	•	이벤트 예시
	•	제목: 오늘의 학습표현
	•	시간: 당일 21:00~21:10 (기본) 또는 종일(all-day) + 설명에 5문장

⸻

15) Django 엔드포인트 예시

# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import DailySet
from django.utils import timezone

@api_view(["GET"])
def today(request):
    ds = DailySet.objects.filter(date=timezone.localdate()).first()
    if not ds:
        return Response({"error":"not_generated"}, status=404)
    return Response(ds.payload)


⸻

16) 서비스워커 푸시 핸들러 예시

// service-worker.js
self.addEventListener('push', event => {
  const data = event.data?.json() || {};
  event.waitUntil(
    self.registration.showNotification(data.notification?.title || '오늘의 일본어', {
      body: data.notification?.body,
      data,
      icon: '/icons/icon-192.png'
    })
  );
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.openWindow('/today'));
});


⸻

17) 보안 체크리스트
	•	OpenAI 키는 서버 환경변수/시크릿 매니저에만 저장. 프론트 절대 노출 금지.
	•	백엔드 도메인 허용 목록(CORS) 최소화, CSRF 설정.
	•	FCM 토큰 탈취·남용 대비: 토큰 해지/재발급, 도메인/서비스워커 스코프 제한.
	•	구글 OAuth refresh_token 암호화 저장.

⸻

18) 테스트 전략
	•	단위: 프롬프트 → JSON 스키마 검증 테스트.
	•	통합: 00:00 배치 모의 실행, 5문장 개수/형식 체크.
	•	E2E: PWA 설치, 푸시 수신, 오늘의 페이지 열람.

⸻

19) 마일스톤 (MVP 2주 가정)
	•	D1~3: Django skeleton, 모델/마이그레이션, /api/today, 관리 커맨드로 수동 생성.
	•	D4~6: OpenAI 연동 + JSON 검증 + DB 저장, 어드민 페이지.
	•	D7~9: FCM 등록/브로드캐스트, 서비스워커, PWA.
	•	D10~12: Google OAuth + Calendar 기록(연결 유저 대상), TTS 버튼.
	•	D13~14: 비용 대시보드, 알림 임계치, 배포(리드미/ENV 템플릿).

⸻

20) 다음 결정 필요 사항
	•	프런트 프레임워크(React vs Django Template) 결정.
	•	캘린더 이벤트 시간을 종일 vs 특정시간 중 선택.
	•	알림 텍스트 포맷(5문장 모두 vs 한 문장 요약)과 매시 발송 방식(동일/랜덤 한 문장).
	•	모델 선택 및 단가(속도 vs 비용) 확정.

⸻

21) 빠른 시작 체크리스트
	•	Django 프로젝트 생성, DRF 설치
	•	Postgres 연결
	•	OpenAI 키/모델 설정
	•	관리 커맨드 generate_daily_set
	•	FCM 웹 세팅 + 서비스워커
	•	/api/today + 간단한 Today 페이지
	•	Google OAuth 연결 + Calendar upsert
	•	비용 로그/대시보드