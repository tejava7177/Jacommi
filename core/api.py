from django.urls import path
from django.http import JsonResponse
from django.utils import timezone
from .models import DailySet

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