from django.db import models
from django.contrib.auth.models import User

class DailySet(models.Model):
    date = models.DateField(unique=True)
    topic = models.CharField(max_length=120, blank=True, default="")
    payload = models.JSONField()  # {date, topic, sentences[ {jp,ko} x5 ], meta}
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.topic}"


class ApiUsageLog(models.Model):
    date = models.DateField()                       # 기준 날짜(로컬)
    model = models.CharField(max_length=64)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["date"]), models.Index(fields=["model"])]

    def __str__(self):
        return f"{self.date} {self.model} ${self.cost_usd}"

class FcmToken(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    token = models.CharField(max_length=350, unique=True)
    platform = models.CharField(max_length=20, default='web')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# Google 계정 OAuth 정보 저장
class GoogleAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    refresh_token = models.TextField(blank=True, default="")
    email = models.EmailField(blank=True, default="")
    calendar_id = models.CharField(max_length=200, default="primary")
    last_event_date = models.DateField(null=True, blank=True)
    photo_url = models.URLField(blank=True, default="")

    def __str__(self):
        return f"{self.email or self.user.username}"


class SavedSentence(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_sentences")
    date = models.DateField()                 # DailySet 날짜
    topic = models.CharField(max_length=200)  # DailySet 토픽(표시용)
    idx = models.IntegerField(default=0)      # 0~4 (몇 번째 문장인지)
    jp = models.TextField()
    ko = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "date", "idx"),)  # 같은 날 같은 위치 문장 중복 저장 방지
        indexes = [
            models.Index(fields=["user", "date"]),
        ]

    def __str__(self):
        return f"[{self.date} #{self.idx}] {self.user.username} - {self.jp[:20]}"