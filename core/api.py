from django.urls import path
from django.http import JsonResponse
from django.utils import timezone
from .models import DailySet

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import GoogleAccount
from .google_calendar import insert_today_event

@require_POST
@login_required
def calendar_insert_today(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=401)

    ga = GoogleAccount.objects.filter(user=request.user).first()
    if not ga:
        return JsonResponse({"ok": False, "error": "google_not_linked"}, status=400)

    today = timezone.localdate()

    # ✅ 중복 방지: 이미 오늘 저장한 적 있음
    if ga.last_event_date == today:
        return JsonResponse({"ok": False, "error": "already_inserted"}, status=409)

    # 실제 삽입
    ok, info = insert_today_event(ga)  # (True, event_id) / (False, "에러메시지")
    if not ok:
        return JsonResponse({"ok": False, "error": "insert_failed", "detail": info}, status=500)

    # 성공 시 오늘로 마킹
    ga.last_event_date = today
    ga.save(update_fields=["last_event_date"])

    return JsonResponse({"ok": True, "event_id": info})


def today_api(request):
    today = timezone.localdate()
    ds = DailySet.objects.filter(date=today).first()
    if not ds:
        # 아직 생성 전이라면 더미(학습 확인용) 반환
        dummy = {
            "date": str(today),
            "topic": "스프린트計画 共有",
            "sentences": [
                {"jp": "今日(きょう)のタスクを共有(きょうゆう)します。", "ko": "오늘의 업무를 공유하겠습니다."},
                {"jp": "進捗(しんちょく)を更新(こうしん)してください。", "ko": "진행 상황을 업데이트해주세요."},
                {"jp": "見積(みつも)りを再確認(さいかくにん)します。", "ko": "견적을 다시 확인하겠습니다."},
                {"jp": "レビュー依頼(いらい)を送付(そうふ)しました。", "ko": "리뷰 요청을 보냈습니다."},
                {"jp": "明日(あした)の会議(かいぎ)に参加(さんか)可能(かのう)ですか。", "ko": "내일 회의 참석 가능하신가요?"},
            ],
            "meta": {"level": "B1-B2", "tags": ["회의", "개발", "공유"]},
        }
        return JsonResponse(dummy)
    return JsonResponse(ds.payload)

urlpatterns = [path("today", today_api, name="api_today")]