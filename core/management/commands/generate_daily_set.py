# core/management/commands/generate_daily_set.py
import os
import json
import random
from datetime import date as date_cls
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import DailySet, ApiUsageLog
from core.usage import estimate_cost


# ==========================
# 1. 토픽 카탈로그 / 프롬프트
# ==========================

# 다양한 장면을 미리 정의해 두고 날짜 기반으로 골라 쓴다.
TOPIC_CATALOG = [
    # 업무 / 회의
    {
        "code": "scrum_planning",
        "jp_topic": "スプリント計画会議",
        "ko_desc": "스프린트 계획 회의",
        "category": "business_meeting",
        "tags": ["회의", "개발", "스크럼"],
    },
    {
        "code": "one_on_one",
        "jp_topic": "１対１のフィードバック面談",
        "ko_desc": "1:1 피드백 면담",
        "category": "business_meeting",
        "tags": ["피드백", "커리어", "멘토링"],
    },
    {
        "code": "online_meeting",
        "jp_topic": "オンライン会議の進行",
        "ko_desc": "온라인 회의 진행",
        "category": "business_meeting",
        "tags": ["온라인", "회의"],
    },

    # 회사 생활 / 잡담
    {
        "code": "office_smalltalk",
        "jp_topic": "オフィスでの何気ない雑談",
        "ko_desc": "사무실에서의 가벼운 잡담",
        "category": "office_life",
        "tags": ["잡담", "동료", "스몰토크"],
    },
    {
        "code": "after_work",
        "jp_topic": "仕事終わりの飲み会",
        "ko_desc": "퇴근 후 회식",
        "category": "office_life",
        "tags": ["회식", "동료", "술자리"],
    },

    # 병원 / 건강
    {
        "code": "hospital_checkup",
        "jp_topic": "病院での健康診断",
        "ko_desc": "병원 건강검진",
        "category": "hospital",
        "tags": ["건강", "병원", "진료"],
    },
    {
        "code": "pharmacy",
        "jp_topic": "薬局での薬の相談",
        "ko_desc": "약국에서 약 상담",
        "category": "hospital",
        "tags": ["약국", "상담"],
    },

    # 음식점
    {
        "code": "restaurant_lunch",
        "jp_topic": "社員食堂でのランチ注文",
        "ko_desc": "사내 식당 점심 주문",
        "category": "restaurant",
        "tags": ["점심", "주문", "음식"],
    },
    {
        "code": "izakaya",
        "jp_topic": "居酒屋での注文と会計",
        "ko_desc": "이자카야에서 주문과 계산",
        "category": "restaurant",
        "tags": ["술집", "주문", "계산"],
    },

    # 쇼핑 / 악기
    {
        "code": "music_shop",
        "jp_topic": "楽器店でのベース購入相談",
        "ko_desc": "악기점에서 베이스 상담",
        "category": "shopping",
        "tags": ["악기", "베이스", "쇼핑"],
    },
    {
        "code": "department_store",
        "jp_topic": "デパートでの服選び",
        "ko_desc": "백화점에서 옷 고르기",
        "category": "shopping",
        "tags": ["패션", "쇼핑"],
    },

    # 여행
    {
        "code": "hotel_checkin",
        "jp_topic": "ホテルでのチェックイン",
        "ko_desc": "호텔 체크인",
        "category": "travel",
        "tags": ["여행", "호텔"],
    },
    {
        "code": "train_station",
        "jp_topic": "駅での乗り換え案内",
        "ko_desc": "역에서 환승 안내 받기",
        "category": "travel",
        "tags": ["교통", "기차", "길찾기"],
    },

    # 스포츠 / 취미
    {
        "code": "gym_training",
        "jp_topic": "ジムでのトレーニング相談",
        "ko_desc": "헬스장에서 운동 상담",
        "category": "hobby_sport",
        "tags": ["운동", "헬스"],
    },
    {
        "code": "sports_watch",
        "jp_topic": "同僚と試合観戦の計画を立てる",
        "ko_desc": "동료와 경기 관람 계획 세우기",
        "category": "hobby_sport",
        "tags": ["스포츠", "관람", "약속"],
    },

    # 감정 / 인간관계
    {
        "code": "say_no_politely",
        "jp_topic": "依頼を丁寧に断る表現",
        "ko_desc": "요청을 정중하게 거절하기",
        "category": "communication",
        "tags": ["거절", "커뮤니케이션", "감정"],
    },
    {
        "code": "appreciation",
        "jp_topic": "感謝をきちんと伝える表現",
        "ko_desc": "감사를 제대로 전달하는 표현",
        "category": "communication",
        "tags": ["감사", "칭찬"],
    },

    # 가족 / 일상
    {
        "code": "family_daily",
        "jp_topic": "家族との日常会話",
        "ko_desc": "가족과의 일상 대화",
        "category": "daily_life",
        "tags": ["가족", "일상"],
    },
    {
        "code": "weather_chat",
        "jp_topic": "天気の話題で会話を始める",
        "ko_desc": "날씨 이야기로 대화 시작하기",
        "category": "daily_life",
        "tags": ["날씨", "스몰토크"],
    },
]

# 요일별로 우선 사용할 카테고리 그룹
# 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일
WEEKDAY_CATEGORY_GROUPS = {
    0: ["business_meeting", "office_life"],          # 월: 회의/회사생활
    1: ["office_life", "communication"],             # 화: 회사 스몰토크, 커뮤니케이션
    2: ["hospital", "daily_life"],                   # 수: 병원/건강 + 일상
    3: ["restaurant", "shopping"],                   # 목: 음식점/쇼핑
    4: ["business_meeting", "hobby_sport"],          # 금: 회의 + 스포츠/취미
    5: ["travel", "hobby_sport"],                    # 토: 여행/취미
    6: ["daily_life", "communication"],              # 일: 일상 + 감정/관계
}


SYSTEM_PROMPT = (
    "あなたは日本のIT企業で働くプロジェクトマネージャー兼、日本語教育の専門家です。"
    "ビジネス現場だけでなく、病院・飲食店・旅行・買い物・スポーツ・感情表現など"
    "さまざまな場面で使える自然な日本語フレーズを教えます。\n\n"
    "【出力形式】\n"
    "必ず **JSON オブジェクト** だけを返してください。\n"
    "{\n"
    '  \"date\": \"YYYY-MM-DD\",                // 오늘 날짜\n'
    '  \"topic\": \"日本語トピックのタイトル\",     // 일본어 주제 제목\n'
    "  \"sentences\": [                        // 정확히 5문장\n"
    "    {\"jp\": \"…日本語文…\", \"ko\": \"…한국어 번역…\"},\n"
    "    … 合計5つ …\n"
    "  ],\n"
    "  \"meta\": {\n"
    "    \"level\": \"B1-B2\",                // 대략적인 CEFR 레벨\n"
    "    \"category\": \"business_meeting / daily_life / travel / hospital など\",\n"
    "    \"tags\": [\"회의\", \"여행\", \"감정\" などのキーワード]\n"
    "  }\n"
    "}\n\n"
    "【スタイル条件】\n"
    "・文体は、基本的に丁寧体（です／ます調）。\n"
    "・漢字には初級〜中級学習者を意識して必要に応じてひらがなを括弧で補足してください。\n"
    "  例： 会議(かいぎ), 依頼(いらい) など。\n"
    "・각 문장은 실제 회화에서 바로 쓸 수 있는 완결된 한 문장이어야 합니다.\n"
    "・한국어 번역은 직역보다는 자연스러운 비즈니스/일상 회화체로 간결하게 써 주세요."
)


def _select_topic(target_date: date_cls, cli_topic: str):
    """
    - cli_topic 이 'auto'(기본)면, 요일별 카테고리 그룹 안에서 로테이션으로 토픽 하나 선택.
    - cli_topic 에 문자열이 들어오면 그대로 사용 (자유 주제 모드).
    """
    # 1) 사용자가 직접 주제를 지정한 경우 → auto 모드가 아님
    if cli_topic and cli_topic.lower() not in ("auto", "자동"):
        topic = cli_topic
        meta = {
            "category": "custom",
            "tags": ["custom"],
            "ko_desc": cli_topic,
        }
        return topic, meta

    # 2) auto 모드: 요일 기반 카테고리 선택
    weekday = target_date.weekday()  # 0=월, 6=일
    cat_group = WEEKDAY_CATEGORY_GROUPS.get(weekday)

    # 혹시 매핑이 없으면 전체 카테고리를 사용
    if not cat_group:
        cat_group = list({t["category"] for t in TOPIC_CATALOG})

    # 선택된 카테고리 그룹 안에서만 토픽 후보 추리기
    candidates = [t for t in TOPIC_CATALOG if t["category"] in cat_group]

    # 그래도 비면 전체에서 사용
    if not candidates:
        candidates = TOPIC_CATALOG

    # 3) 로테이션: 기준일로부터의 일수로 인덱스 계산
    base = date_cls(2025, 1, 1)  # 서비스 기준일 (원하면 바꿔도 됨)
    delta_days = (target_date - base).days
    idx = delta_days % len(candidates)
    topic_def = candidates[idx]

    topic = topic_def["jp_topic"]
    meta = {
        "category": topic_def["category"],
        "tags": topic_def["tags"],
        "ko_desc": topic_def["ko_desc"],
        "code": topic_def["code"],
    }
    return topic, meta


def _build_user_prompt(date_str: str, topic: str, topic_meta: dict) -> str:
    """
    모델에게 오늘 날짜 + 선택된 토픽 + 장면 정보를 모두 넘겨준다.
    """
    ko_desc = topic_meta.get("ko_desc", "")
    category = topic_meta.get("category", "")
    tags = ", ".join(topic_meta.get("tags", []))

    return (
        f"오늘 날짜는 {date_str} 입니다.\n"
        f"장면(category): {category}\n"
        f"한국어 설명: {ko_desc}\n"
        f"일본어 토픽 제목: 「{topic}」 로 설정합니다.\n"
        f"관련 키워드(tags): {tags}\n\n"
        "요구사항:\n"
        "1. 위 장면을 바탕으로, 실제 일본인과 대화할 때 바로 쓸 수 있는 자연스러운 문장을 만들어 주세요.\n"
        "2. 정확히 5문장만 생성합니다.\n"
        "3. 가능한 한 서로 다른 상황/뉘앙스를 섞어서, 표현의 폭이 넓어지도록 해 주세요.\n"
        "   - 예: 요청, 제안, 정중한 거절, 질문, 감사 표현 등\n"
        "4. 각 문장은 1문장으로 완결되며, 너무 길지 않게(2줄 이내) 유지해 주세요.\n"
        "5. 위에서 설명한 JSON 스키마 형식을 반드시 지켜 주세요."
    )


def _fallback_dummy(date_str: str, topic: str, topic_meta: dict):
    """
    OpenAI 호출 실패 시 사용하는 더미 데이터.
    토픽/메타도 함께 반영해 둔다.
    """
    return {
        "date": date_str,
        "topic": topic or "スプリント計画 会議",
        "sentences": [
            {
                "jp": "今日(きょう)の計画(けいかく)を共有(きょうゆう)します。",
                "ko": "오늘 계획을 공유하겠습니다.",
            },
            {
                "jp": "進捗(しんちょく)を簡潔(かんけつ)に報告(ほうこく)してください。",
                "ko": "진척을 간단히 보고해주세요.",
            },
            {
                "jp": "優先度(ゆうせんど)を再確認(さいかくにん)します。",
                "ko": "우선순위를 다시 확인하겠습니다.",
            },
            {
                "jp": "見積(みつも)りの根拠(こんきょ)を明確(めいかく)にします。",
                "ko": "견적의 근거를 명확히 하겠습니다.",
            },
            {
                "jp": "懸念点(けねんてん)があれば共有(きょうゆう)してください。",
                "ko": "우려 사항이 있으면 공유해주세요.",
            },
        ],
        "meta": {
            "level": "B1-B2",
            "category": topic_meta.get("category", "fallback"),
            "tags": topic_meta.get("tags", ["회의", "개발", "스프린트"]),
            "ko_desc": topic_meta.get("ko_desc", "더미 데이터"),
        },
    }


# ==========================
# 2. Django 관리 명령
# ==========================

class Command(BaseCommand):
    help = "Generate and store today's 5 JP sentences (다양한 장면, idempotent)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--topic",
            default="auto",
            help="주제. 기본값 'auto' 는 날짜별로 자동 선택. "
                 "직접 입력하면 해당 문자열을 주제로 사용합니다.",
        )
        parser.add_argument(
            "--date",
            default=None,
            help="YYYY-MM-DD 로 특정 날짜 생성",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="이미 있어도 재생성(기존 레코드 덮어씀)",
        )

    def handle(self, *args, **opts):
        # 날짜 결정
        if opts.get("date"):
            try:
                target_date = date_cls.fromisoformat(opts["date"])
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid --date. Use YYYY-MM-DD"))
                return
        else:
            target_date = timezone.localdate()

        # 토픽/메타 선택
        cli_topic = opts["topic"]
        topic, topic_meta = _select_topic(target_date, cli_topic)
        force = bool(opts.get("force"))

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # 이미 존재하는지 확인
        exists = DailySet.objects.filter(date=target_date).exists()
        if exists and not force:
            self.stdout.write(self.style.WARNING(f"Already exists for {target_date}"))
            return
        if exists and force:
            DailySet.objects.filter(date=target_date).delete()
            ApiUsageLog.objects.filter(date=target_date, model=model_name).delete()

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        date_str = target_date.isoformat()

        # -----------------
        #  API 키 없음 → 더미
        # -----------------
        if not api_key:
            data = _fallback_dummy(date_str, topic, topic_meta)
            DailySet.objects.create(
                date=target_date,
                topic=data.get("topic", ""),
                payload=data,
            )
            ApiUsageLog.objects.create(
                date=target_date,
                model=model_name,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                cost_usd=Decimal("0"),
                meta={"reason": "no_api_key", "topic": topic, **topic_meta},
            )
            self.stdout.write(self.style.SUCCESS("Generated (dummy, no OPENAI_API_KEY)"))
            return

        # -----------------
        #  실제 OpenAI 호출
        # -----------------
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            msgs = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_user_prompt(date_str, topic, topic_meta),
                },
            ]

            resp = client.chat.completions.create(
                model=model_name,
                messages=msgs,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            data = json.loads(content)

            # 간단 검증
            s = data.get("sentences", [])
            if not (isinstance(s, list) and len(s) == 5):
                raise ValueError("Invalid JSON format from model (sentences length != 5)")

            # 주제 필드는 모델이 임의로 바꿔도 상관없지만,
            # 우리가 선택한 토픽도 payload.meta 에 같이 넣어둔다.
            meta = data.get("meta") or {}
            meta.setdefault("category", topic_meta.get("category"))
            meta.setdefault("tags", topic_meta.get("tags"))
            meta.setdefault("ko_desc", topic_meta.get("ko_desc"))
            data["meta"] = meta

            DailySet.objects.create(
                date=target_date,
                topic=data.get("topic", topic),
                payload=data,
            )

            # usage/cost logging
            usage = getattr(resp, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = (
                getattr(usage, "total_tokens", prompt_tokens + completion_tokens)
                if usage
                else (prompt_tokens + completion_tokens)
            )
            cost = estimate_cost(model_name, prompt_tokens, completion_tokens)

            ApiUsageLog.objects.create(
                date=target_date,
                model=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                meta={"topic": topic, **topic_meta},
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Generated (OpenAI) tokens={total_tokens} cost=${cost}"
                )
            )
            return

        except Exception as e:
            # 실패 시 더미로라도 저장해서 서비스는 계속 동작
            data = _fallback_dummy(date_str, topic, topic_meta)
            DailySet.objects.create(
                date=target_date,
                topic=data.get("topic", ""),
                payload=data,
            )
            ApiUsageLog.objects.create(
                date=target_date,
                model=model_name,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                cost_usd=Decimal("0"),
                meta={"fallback_error": str(e), "topic": topic, **topic_meta},
            )
            self.stdout.write(
                self.style.WARNING(f"OpenAI failed, fallback dummy used: {e}")
            )