
# test_request.py
import requests
import json

URL = "https://389494a94da3.ngrok-free.app/api/chat-assistant"  # ajuste a porta se necessário

payload = {
    "message": "Como posso usar o MediaCuts Studio?",
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(URL, headers=headers, data=json.dumps(payload))
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))
except Exception as e:
    print("Erro ao enviar requisição:", e)
