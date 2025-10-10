from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from .models import DailySet
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FcmToken

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
            defaults={"active": True, "platform": "web"},
        )
        return JsonResponse({"ok": True, "created": created})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)