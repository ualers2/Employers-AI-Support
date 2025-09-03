import os
import requests
from dotenv import load_dotenv

# Carrega variáveis do .env (ajuste o caminho se necessário)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'modules', 'Keys', 'keys.env'))

SERVER_URL = os.getenv('WA_SERVER_URL')      
INSTANCE_ID = os.getenv('WA_INSTANCE_NAME')     
API_KEY     = os.getenv('WA_API_KEY')        
GROUP_JID   = os.getenv('WA_SUPPORT_GROUP_JID')  
print(SERVER_URL)
print(INSTANCE_ID)
print(API_KEY)
print(GROUP_JID)

url = f"{SERVER_URL.rstrip('/')}/message/sendText/{INSTANCE_ID}"

payload = {
    "number": GROUP_JID,
    "options": {
        "delay": 500,                  # tempo em ms antes de enviar
        "presence": "composing",       # mostra "digitando..."
        "linkPreview": True,           # pré‑visualiza links
        # Exemplo de citação de mensagem anterior (opcional):
        # "quoted": {
        #     "key": {
        #         "remoteJid": GROUP_JID,
        #         "fromMe": True,
        #         "id": "BAE594145F4C59B4",
        #         "participant": "<string>"
        #     },
        #     "message": {"conversation": "Texto da mensagem citada"}
        # },
        # Exemplo de menções (opcional):
        # "mentions": {
        #     "everyOne": True,
        #     "mentioned": ["5511999998888@s.whatsapp.net"]
        # }
    },
    "textMessage": {
        "text": "Olá, grupo de suporte!"
    }
}

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

# Verifica HTTP status e imprime resposta JSON
print(f"Status HTTP: {response.status_code}")
print("Corpo da resposta:", response.json())
