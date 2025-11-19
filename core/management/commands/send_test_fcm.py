# core/management/commands/send_test_fcm.py

import os

from django.core.management.base import BaseCommand

import firebase_admin
from firebase_admin import credentials, messaging


def _init_firebase():
    """
    management command에서 단독으로 실행해도
    firebase_admin 이 한 번만 초기화되도록 처리.
    """
    if firebase_admin._apps:
        return

    cred_path = os.getenv("FIREBASE_CREDENTIALS_JSON_PATH")
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError(
            f"FIREBASE_CREDENTIALS_JSON_PATH not found: {cred_path!r}"
        )

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


class Command(BaseCommand):
    help = "지정한 FCM 토큰으로 테스트 푸시를 즉시 전송합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--token",
            required=True,
            help="브라우저에서 발급받은 FCM 등록 토큰",
        )

    def handle(self, *args, **options):
        token = options["token"]

        _init_firebase()

        # 간단한 테스트 메시지
        message = messaging.Message(
            token=token,
            notification=messaging.Notification(
                title="Jacommi 테스트 푸시 ✨",
                body="이 알림이 보이면 브라우저 FCM 연동이 잘 된 거야!",
            ),
            data={
                "kind": "test",
                "source": "send_test_fcm",
            },
        )

        response = messaging.send(message)
        self.stdout.write(self.style.SUCCESS(f"Sent test push. response={response}"))