import os, json
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
    state = request.session.get("google_oauth_state")
    # Validate state to mitigate CSRF
    if request.GET.get("state") != state:
        return JsonResponse({"ok": False, "error": "invalid_state"}, status=400)
    flow = build_flow(state=state)
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    creds = flow.credentials  # includes access_token, refresh_token (if consent)
    refresh_token = getattr(creds, "refresh_token", None)
    access_token = creds.token

    # 사용자 정보 조회 (id_token)
    try:
        idinfo = id_token.verify_oauth2_token(
            creds.id_token, grequests.Request(), os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        )
        email = idinfo.get("email")
    except Exception:
        # id_token 없는 경우 userinfo 엔드포인트 대체도 가능(여기선 단순 처리)
        email = None

    # 간단히: 로그인된 Django user가 없으면 superuser 계정으로 연결하거나
    # 또는 이메일로 local user를 만들자(프로토타입)
    if not request.user.is_authenticated:
        # 이메일 기반 dummy 유저 연결 (실서비스에선 proper 로그인 프로세스 권장)
        if email:
            user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        else:
            user, _ = User.objects.get_or_create(username=f"google_{timezone.now().timestamp()}")
    else:
        user = request.user

    # Ensure the Django session is authenticated with this user
    try:
        login(request, user)
    except Exception:
        pass

    # Preserve existing refresh token if not returned this time
    existing_ga = GoogleAccount.objects.filter(user=user).first()
    if not refresh_token and existing_ga and existing_ga.refresh_token:
        refresh_token = existing_ga.refresh_token

    # Google Calendar 기본 캘린더 ID 가져오기 (선택)
    try:
        service = build("calendar", "v3", credentials=creds)
        cal_list = service.calendarList().list(maxResults=1).execute()
        calendar_id = cal_list["items"][0]["id"] if cal_list.get("items") else "primary"
    except Exception:
        calendar_id = "primary"

    # DB upsert
    GoogleAccount.objects.update_or_create(
        user=user,
        defaults={
            "refresh_token": refresh_token or (existing_ga.refresh_token if existing_ga else ""),  # 첫 동의 시에만 제공 가능
            "email": email or "",
            "calendar_id": calendar_id,
            "last_event_date": None,
        },
    )

    # 완료 후 리다이렉트 (홈으로)
    return HttpResponseRedirect("/")