from django.db import models

class DailySet(models.Model):
    date = models.DateField(unique=True)
    topic = models.CharField(max_length=120, blank=True, default="")
    payload = models.JSONField()  # {date, topic, sentences[ {jp,ko} x5 ], meta}
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.topic}"