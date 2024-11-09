# app/views/health.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "OK"}, status=200)
