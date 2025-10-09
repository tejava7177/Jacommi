from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from .models import DailySet

def health(request):
    return JsonResponse({"status": "ok"})

def home(request):
    today = timezone.localdate()
    ds = DailySet.objects.filter(date=today).first()
    payload = ds.payload if ds else None
    return render(request, "index.html", {"payload": payload})