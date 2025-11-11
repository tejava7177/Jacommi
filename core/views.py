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