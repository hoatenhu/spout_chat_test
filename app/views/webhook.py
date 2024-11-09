import json
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from app.helpers.conversation import create_conversation


WA_ACCESS_TOKEN = config("WA_ACCESS_TOKEN")
WA_CONFIG_TOKEN = config("WA_CONFIG_TOKEN")
SPOUT_PHONE_NUMBER_ID = config("SPOUT_PHONE_NUMBER_ID")

@csrf_exempt
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        challenge = request.GET.get("hub.challenge")
        token = request.GET.get("hub.verify_token")
        if mode == "subscribe" and token == WA_CONFIG_TOKEN:
            return HttpResponse(challenge, status=200)
        return HttpResponse(status=403)

    elif request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        print("Received data:", json.dumps(data, indent=2))
        customer_id = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('contacts', [{}])[0].get('wa_id')
        if customer_id:
            conversation_id = create_conversation(customer_id)
            if conversation_id is None:
                return JsonResponse({'error': 'Failed to access Conversations table'}, status=500)
        return JsonResponse({'status': 'received'}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def send_whatsapp_message(phone_number, text):
    if not WA_ACCESS_TOKEN or not SPOUT_PHONE_NUMBER_ID:
        print("Error: Access token or phone number ID is not defined.")
        return {"error": "Missing credentials"}
    
    url = f"https://graph.facebook.com/v20.0/{SPOUT_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_ACCESS_TOKEN}", 
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {"body": text}
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def send_message_to_customer(request):
    data = json.loads(request.body.decode('utf-8'))
    phone_number = data.get('phoneNumber')
    text = data.get('text')

    if not phone_number or not text:
        return JsonResponse({'error': 'phone_number and text are required'}, status=400)

    response = send_whatsapp_message(phone_number, text)
    return JsonResponse(response, status=200)