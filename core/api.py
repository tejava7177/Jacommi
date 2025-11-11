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
    """
    오늘의 문장을 Google Calendar에 등록하는 API
    """
    acc = GoogleAccount.objects.filter(user=request.user).first()
    if not acc or not acc.refresh_token:
        return JsonResponse({"ok": False, "error": "google_not_linked"}, status=400)

    try:
        result = insert_today_event(acc)
        return JsonResponse({"ok": True, "result": result})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


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