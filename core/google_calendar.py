# core/google_calendar.py
import os
from datetime import datetime, timedelta, date as date_cls

from django.utils import timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from .models import GoogleAccount, DailySet


def get_google_service(account: GoogleAccount):
    """
    refresh_token 으로 access token 을 갱신해서
    구글 캘린더 service 객체를 만들어 반환한다.
    """
    creds = Credentials(
        None,
        refresh_token=account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    )
    creds.refresh(Request())
    return build("calendar", "v3", credentials=creds)


def insert_today_event(account: GoogleAccount) -> dict:
    """
    오늘 날짜의 DailySet 한 개를 사용해
    account 가 가진 캘린더에 이벤트를 한 개 추가한다.

    반환 형식(항상 dict):

    - 성공:
        {"ok": True, "created": True, "htmlLink": "https://..."}
    - 이미 오늘 삽입된 경우:
        {"ok": False, "reason": "already_exists"}
    - DailySet 이 없는 경우:
        {"ok": False, "reason": "no_daily_set"}
    - 그 외 에러는 예외로 던짐(뷰에서 try/except 처리)
    """
    today = timezone.localdate()

    # 이미 오늘 이벤트를 넣었다면(마지막 기록으로 체크)
    if account.last_event_date == today:
        return {"ok": False, "reason": "already_exists"}

    daily = DailySet.objects.filter(date=today).first()
    if not daily:
        return {"ok": False, "reason": "no_daily_set"}

    payload = daily.payload or {}
    sentences = payload.get("sentences", [])
    topic = payload.get("topic") or "今日の日本語フレーズ"

    # 제목은 토픽 + 날짜 정도로
    summary = f"[Jacommi] {topic}"
    # 본문: 일본어 + 한국어를 적당히 붙여서 넣어준다
    lines = []
    for idx, s in enumerate(sentences, start=1):
        jp = s.get("jp") or ""
        ko = s.get("ko") or ""
        lines.append(f"{idx}. {jp}\n   - {ko}")
    description = "\n\n".join(lines)

    service = get_google_service(account)

    event_body = {
        "summary": summary,
        "description": description,
        "start": {"date": str(today)},  # 종일 이벤트
        "end": {"date": str(today)},
    }

    event = service.events().insert(
        calendarId=account.calendar_id or "primary",
        body=event_body,
    ).execute()

    account.last_event_date = today
    account.save(update_fields=["last_event_date"])

    return {
        "ok": True,
        "created": True,
        "htmlLink": event.get("htmlLink"),
    }