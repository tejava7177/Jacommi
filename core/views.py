from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from .models import DailySet
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FcmToken
from django.shortcuts import render
from django.utils import timezone
from .models import DailySet, GoogleAccount

import json
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required

from .models import DailySet, GoogleAccount, SavedSentence

from django.contrib.auth import logout
from django.shortcuts import redirect

def health(request):
    return JsonResponse({"status": "ok"})

def home(request):
    today = timezone.localdate()
    ds = DailySet.objects.filter(date=today).first()
    payload = ds.payload if ds else None
    return render(request, "index.html", {"payload": payload})

@csrf_exempt
def fcm_register(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        token = data.get("token")
        if not token:
            return JsonResponse({"ok": False, "error": "no_token"}, status=400)
        # 사용자 로그인 연동 시 user=request.user if request.user.is_authenticated else None
        obj, created = FcmToken.objects.update_or_create(
            token=token,
            defaults={
                "active": True,
                "platform": "web",
                "user": request.user if request.user.is_authenticated else None,
            },
        )
        return JsonResponse({"ok": True, "created": created})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

@csrf_exempt
def fcm_unregister(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        token = data.get("token")
        if not token:
            return JsonResponse({"ok": False, "error": "no_token"}, status=400)

        # 비활성화(soft delete) 처리: active=False
        updated = FcmToken.objects.filter(token=token).update(active=False)
        # 사용자가 로그인한 상태라면 해당 사용자 토큰만 제한적으로 비활성화하도록 하고 싶다면:
        # if request.user.is_authenticated:
        #     updated = FcmToken.objects.filter(token=token, user=request.user).update(active=False)

        return JsonResponse({"ok": True, "updated": updated})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


def today_page(request):
    ds = DailySet.objects.filter(date=timezone.localdate()).first()
    ga = None
    if request.user.is_authenticated:
        ga = GoogleAccount.objects.filter(user=request.user).first()
    return render(request, "index.html", {
        "payload": ds.payload if ds else None,
        "ga": ga,
    })


@login_required
def mypage(request):
    items = (
        SavedSentence.objects
        .filter(user=request.user)
        .order_by("-date", "idx", "-created_at")
    )
    return render(request, "mypage.html", {"items": items})


@login_required
@require_POST
@csrf_protect
def api_sentence_save(request):
    """
    body: {date: 'YYYY-MM-DD', topic, idx:0..4, jp, ko}
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        date_str = data.get("date")
        topic = data.get("topic") or ""
        idx = int(data.get("idx", 0))
        jp = (data.get("jp") or "").strip()
        ko = (data.get("ko") or "").strip()
        if not (date_str and jp):
            return JsonResponse({"ok": False, "error": "bad_request"}, status=400)

        from datetime import date as _date
        y, m, d = [int(x) for x in date_str.split("-")]
        ddate = _date(y, m, d)

        obj, created = SavedSentence.objects.get_or_create(
            user=request.user, date=ddate, idx=idx,
            defaults={"topic": topic, "jp": jp, "ko": ko},
        )
        # 이미 있더라도 문장이 바뀌었으면 업데이트(선택)
        if not created and (obj.jp != jp or obj.ko != ko or obj.topic != topic):
            obj.jp = jp
            obj.ko = ko
            obj.topic = topic
            obj.save(update_fields=["jp", "ko", "topic"])

        return JsonResponse({"ok": True, "created": created, "id": obj.id})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@login_required
@require_POST
@csrf_protect
def api_sentence_delete(request, sentence_id: int):
    # 본인 소유 문장만 삭제
    obj = SavedSentence.objects.filter(id=sentence_id, user=request.user).first()
    if not obj:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)
    obj.delete()
    return JsonResponse({"ok": True})

def logout_view(request):
    """
    간단 로그아웃 후 메인 페이지(/)로 리다이렉트
    """
    logout(request)
    return redirect("/")