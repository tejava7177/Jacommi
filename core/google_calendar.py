import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from .models import GoogleAccount, DailySet


def get_google_service(account: GoogleAccount):
    """refresh_token으로 인증 갱신 후 service 객체 반환"""
    creds = Credentials(
        None,
        refresh_token=account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    )
    creds.refresh(Request())
    service = build("calendar", "v3", credentials=creds)
    return service


def insert_today_event(account: GoogleAccount):
    """오늘의 학습 문장을 구글 캘린더에 등록"""
    from django.utils import timezone
    today = timezone.localdate()
    daily = DailySet.objects.filter(date=today).first()
    if not daily:
        return "No daily set found."

    service = get_google_service(account)

    # 이벤트 제목/내용 구성
    summary = "오늘의 일본어 회화 5문장 🇯🇵"
    description = "\n".join([f"{i+1}. {s['jp']} — {s['ko']}" for i, s in enumerate(daily.payload["sentences"])])

    event_body = {
        "summary": summary,
        "description": description,
        "start": {"date": str(today)},
        "end": {"date": str(today)},
    }

    event = service.events().insert(
        calendarId=account.calendar_id or "primary",
        body=event_body
    ).execute()

    account.last_event_date = today
    account.save(update_fields=["last_event_date"])

    return f"Event created: {event.get('id')}"