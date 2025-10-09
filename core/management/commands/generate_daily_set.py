import os
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import DailySet

SYSTEM_PROMPT = (
    "당신은 일본 IT 기업 현업 PM 겸 일본어 교육 전문가입니다. "
    "각 문장은 한자에 히라가나를 괄호로 병기하고, 간결한 한국어 번역을 제공합니다. "
    "출력은 JSON 스키마로만 반환하세요: "
    "{date, topic, sentences[ {jp, ko} x5 ], meta{ level, tags[] }} "
    "문장 톤은 정중체(です/ます調)로 자연스럽게."
)

def _build_user_prompt(date_str: str, topic: str) -> str:
    return (
        f"오늘 날짜는 {date_str}, 주제는 '{topic}'. 난이도 B1-B2.\n"
        "정확히 5문장을 생성하세요."
    )

def _fallback_dummy(date_str: str):
    return {
        "date": date_str,
        "topic": "スプリント計画 共有",
        "sentences": [
            {"jp": "今日(きょう)の計画(けいかく)を共有(きょうゆう)します。", "ko": "오늘 계획을 공유하겠습니다."},
            {"jp": "進捗(しんちょく)を簡潔(かんけつ)に報告(ほうこく)してください。", "ko": "진척을 간단히 보고해주세요."},
            {"jp": "優先度(ゆうせんど)を再確認(さいかくにん)します。", "ko": "우선순위를 다시 확인하겠습니다."},
            {"jp": "見積(みつも)りの根拠(こんきょ)を明確(めいかく)にします。", "ko": "견적의 근거를 명확히 하겠습니다."},
            {"jp": "懸念点(けねんてん)があれば共有(きょうゆう)してください。", "ko": "우려 사항이 있으면 공유해주세요."},
        ],
        "meta": {"level": "B1-B2", "tags": ["회의", "개발", "스프린트"]},
    }

class Command(BaseCommand):
    help = "Generate and store today's 5 JP business sentences (idempotent)"

    def add_arguments(self, parser):
        parser.add_argument("--topic", default="スプリント計画 会議", help="주제(기본: 스프린트 계획 회의)")

    def handle(self, *args, **opts):
        date = timezone.localdate()
        topic = opts["topic"]

        if DailySet.objects.filter(date=date).exists():
            self.stdout.write(self.style.WARNING(f"Already exists for {date}"))
            return

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            data = _fallback_dummy(date.isoformat())
            DailySet.objects.create(date=date, topic=data.get("topic", ""), payload=data)
            self.stdout.write(self.style.SUCCESS("Generated (dummy, no OPENAI_API_KEY)"))
            return

        # 실제 OpenAI 호출
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            msgs = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(date.isoformat(), topic)},
            ]
            resp = client.chat.completions.create(
                model="gpt-5.1-mini",
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

            DailySet.objects.create(date=date, topic=data.get("topic", ""), payload=data)
            self.stdout.write(self.style.SUCCESS("Generated (OpenAI)"))

        except Exception as e:
            # 실패 시 더미로라도 저장해서 서비스는 계속 동작
            data = _fallback_dummy(date.isoformat())
            DailySet.objects.create(date=date, topic=data.get("topic", ""), payload=data)
            self.stdout.write(self.style.WARNING(f"OpenAI failed, fallback dummy used: {e}"))