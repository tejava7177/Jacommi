from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.urls import path
from .models import ApiUsageLog

# ✅ usage_summary 함수 먼저 정의
@api_view(["GET"])
@permission_classes([IsAdminUser])
def usage_summary(request):
    try:
        days = int(request.GET.get("days", "30"))
    except ValueError:
        days = 30
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    qs = ApiUsageLog.objects.filter(date__gte=start, date__lte=today)
    totals = qs.aggregate(
        prompt=Sum("prompt_tokens"),
        completion=Sum("completion_tokens"),
        total=Sum("total_tokens"),
        cost=Sum("cost_usd"),
    )
    by_date = (
        qs.values("date")
        .order_by("date")
        .annotate(
            prompt=Sum("prompt_tokens"),
            completion=Sum("completion_tokens"),
            total=Sum("total_tokens"),
            cost=Sum("cost_usd"),
        )
    )

    return Response({
        "range": {"start": str(start), "end": str(today), "days": days},
        "totals": {
            "prompt_tokens": totals["prompt"] or 0,
            "completion_tokens": totals["completion"] or 0,
            "total_tokens": totals["total"] or 0,
            "cost_usd": str(totals["cost"] or 0),
        },
        "by_date": [
            {
                "date": str(r["date"]),
                "prompt_tokens": r["prompt"] or 0,
                "completion_tokens": r["completion"] or 0,
                "total_tokens": r["total"] or 0,
                "cost_usd": str(r["cost"] or 0),
            }
            for r in by_date
        ],
    })

urlpatterns = [
    path("usage", usage_summary, name="admin_usage"),
]