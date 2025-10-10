from django.core.management.base import BaseCommand
from core.models import GoogleAccount
from core.google_calendar import insert_today_event

class Command(BaseCommand):
    help = "오늘의 일본어 회화 문장을 Google Calendar에 자동 등록합니다."

    def handle(self, *args, **options):
        accounts = GoogleAccount.objects.all()
        for acc in accounts:
            result = insert_today_event(acc)
            self.stdout.write(self.style.SUCCESS(f"[{acc.email}] {result}"))