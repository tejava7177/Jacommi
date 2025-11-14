# core/api.py (또는 views.py 안의 일부로)
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .models import GoogleAccount
from .google_calendar import insert_today_event


@require_POST
@login_required
def calendar_insert_today(request):
    """
    로그인한 사용자의 GoogleAccount 를 찾아
    오늘 DailySet 내용을 캘린더에 1회 저장한다.
    """
    ga = GoogleAccount.objects.filter(user=request.user).first()
    if not ga or not ga.refresh_token:
        return JsonResponse(
            {"ok": False, "error": "no_google_auth"},
            status=400,
        )

    try:
        result = insert_today_event(ga)
    except Exception as e:
        # 디버깅 편하게 로그를 찍고 싶으면 여기서 print 또는 logger 사용
        return JsonResponse(
            {"ok": False, "error": "server_error", "detail": str(e)},
            status=500,
        )

    # insert_today_event 는 항상 dict 를 반환한다고 가정
    if not isinstance(result, dict):
        return JsonResponse(
            {"ok": False, "error": "invalid_result"},
            status=500,
        )

    # 이미 오늘 것 있음 → 409
    if not result.get("ok") and result.get("reason") == "already_exists":
        return JsonResponse(
            {"ok": False, "error": "already_exists"},
            status=409,
        )

    # DailySet 이 없는 경우 → 404 (프론트에서 "오늘 문장이 아직 생성되지 않았어요" 안내 가능)
    if not result.get("ok") and result.get("reason") == "no_daily_set":
        return JsonResponse(
            {"ok": False, "error": "no_daily_set"},
            status=404,
        )

    # 정상 저장
    if result.get("ok"):
        return JsonResponse(
            {
                "ok": True,
                "link": result.get("htmlLink"),
            }
        )

    # 그 외 기타 실패
    return JsonResponse(
        {"ok": False, "error": result.get("reason", "unknown")},
        status=400,
    )