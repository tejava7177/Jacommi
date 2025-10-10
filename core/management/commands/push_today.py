from django.core.management.base import BaseCommand
from django.utils import timezone
import os
from firebase_admin import messaging
from core.models import DailySet, FcmToken
from core.firebase_client import get_app

class Command(BaseCommand):
    help = "Send FCM push with today's topic to all active web tokens"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Do not send, just print summary")

    def handle(self, *args, **opts):
        # Firebase Admin 초기화
        get_app()

        today = timezone.localdate()
        ds = DailySet.objects.filter(date=today).first()
        if not ds:
            self.stdout.write(self.style.WARNING("No DailySet for today"))
            return

        title = f"오늘의 일본어 ({today})"
        body = ds.topic or "오늘의 5문장을 확인해보세요"

        tokens = list(FcmToken.objects.filter(active=True).values_list("token", flat=True))
        if not tokens:
            self.stdout.write(self.style.WARNING("No FCM tokens"))
            return

        if opts.get("dry_run"):
            self.stdout.write(self.style.SUCCESS(f"[DRY] would send to {len(tokens)} tokens: {title} / {body}"))
            return

        # 500개 단위로 분할 발송
        batch_size = 500
        success = 0
        for i in range(0, len(tokens), batch_size):
            chunk = tokens[i:i + batch_size]

            # Build Webpush config (avoid HTTPS link requirement in local dev)
            origin = os.getenv("PUBLIC_WEB_ORIGIN")  # e.g., https://yourdomain.com in production
            webpush_kwargs = {
                "notification": messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon="/static/icon-192.png",  # optional
                )
            }
            if origin and origin.startswith("https://"):
                webpush_kwargs["fcm_options"] = messaging.WebpushFCMOptions(link=f"{origin}/")

            webpush_cfg = messaging.WebpushConfig(**webpush_kwargs)

            msg = messaging.MulticastMessage(
                tokens=chunk,
                webpush=webpush_cfg,
                # Fallback for clients reading from data in foreground/background
                data={
                    "title": title,
                    "body": body,
                },
            )

            res = messaging.send_each_for_multicast(msg)
            success += sum(1 for r in res.responses if r.success)

        self.stdout.write(self.style.SUCCESS(f"Push sent: {success}/{len(tokens)} success"))