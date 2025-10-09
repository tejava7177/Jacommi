from django.db import models

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