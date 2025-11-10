import os, json
import requests
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from googleapiclient.discovery import build
from .google_oauth import build_flow
from .models import GoogleAccount
from django.contrib.auth.models import User
from django.contrib.auth import login


# 1) 로그인 시작: 구글 동의 화면으로 리다이렉트
def google_login(request):
    flow = build_flow()
    # offline access + 재동의 유도: refresh_token 확보를 위해 꼭 필요
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["google_oauth_state"] = state
    return HttpResponseRedirect(auth_url)

# 2) 콜백: 토큰 교환 & DB 저장
@csrf_exempt  # GET만 오므로 CSRF 문제 없음(템플릿 POST 안 함)
def google_callback(request):
    # 1) state 검증 + 재사용 방지
    state = request.session.pop("google_oauth_state", None)
    if request.GET.get("state") != state:
        return JsonResponse({"ok": False, "error": "invalid_state"}, status=400)

    # 2) 토큰 교환
    flow = build_flow(state=state)
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    creds = flow.credentials
    refresh_token = getattr(creds, "refresh_token", None)
    access_token = creds.token

    # 3) 이메일 파악(id_token) + UserInfo로 프로필 보강
    email = None
    try:
        idinfo = id_token.verify_oauth2_token(
            creds.id_token, grequests.Request(), os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        )
        email = idinfo.get("email")
    except Exception:
        pass

    userinfo, picture, display_name = {}, "", ""
    try:
        ui_res = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        if ui_res.ok:
            userinfo = ui_res.json()
            email = email or userinfo.get("email")
            picture = userinfo.get("picture") or ""
            display_name = userinfo.get("name") or ""
    except Exception:
        pass

    # 4) 로컬 유저 준비 + 세션 로그인
    if not request.user.is_authenticated:
        if email:
            user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        else:
            user, _ = User.objects.get_or_create(username=f"google_{timezone.now().timestamp()}")
    else:
        user = request.user

    try:
        login(request, user)
    except Exception:
        pass

    # 5) 기존 refresh_token 보존
    existing_ga = GoogleAccount.objects.filter(user=user).first()
    if not refresh_token and existing_ga and existing_ga.refresh_token:
        refresh_token = existing_ga.refresh_token

    # 6) 기본 캘린더 id 확보(실패 시 primary)
    try:
        service = build("calendar", "v3", credentials=creds)
        cal_list = service.calendarList().list(maxResults=1).execute()
        calendar_id = cal_list["items"][0]["id"] if cal_list.get("items") else "primary"
    except Exception:
        calendar_id = "primary"

    # 7) GoogleAccount upsert (+ 사진 저장)
    GoogleAccount.objects.update_or_create(
        user=user,
        defaults={
            "refresh_token": refresh_token or (existing_ga.refresh_token if existing_ga else ""),
            "email": email or (existing_ga.email if existing_ga else ""),
            "calendar_id": calendar_id,
            "last_event_date": None,
            "photo_url": picture or (getattr(existing_ga, "photo_url", "") if existing_ga else ""),
        },
    )

    # 8) 표시 이름을 로컬 User에 반영(선택)
    if display_name and (not user.first_name and not user.last_name):
        try:
            user.first_name = display_name
            user.save(update_fields=["first_name"])
        except Exception:
            pass

    return HttpResponseRedirect("/")