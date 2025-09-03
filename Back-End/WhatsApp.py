import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# IMPORT SoftwareAI Alfred e Firebase
from Alfred import Alfred
from modules.Keys.Firebase.FirebaseApp import init_firebase
import firebase_admin
from firebase_admin import db
from modules.logger import setup_logger  # Importa o logger

# Carrega variáveis de ambiente
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'modules', 'Keys', 'keys.env'))

# Inicializa Firebase
app_1 = init_firebase()
wa_status_ref   = db.reference('alfred_status/WhatsAppEvolution', app=app_1)
messages_db_ref = db.reference('messages', app=app_1)
configurations_db_ref = db.reference('configurations', app=app_1) 

data = configurations_db_ref.get()
SERVER_URL = data.get("waServerUrl") 
INSTANCE_NAME =  data.get("waInstanceId")
API_KEY = data.get("waApiKey") 
GROUP_JID =  data.get("waSupportGroupJid")

app = FastAPI()


# Cria o logger
log = setup_logger("whatsapp_webhook", "webhook.log")

log.info(f"SERVER_URL{SERVER_URL}")
log.info(f"INSTANCE_NAME{INSTANCE_NAME}")
log.info(f"API_KEY{API_KEY}")
log.info(f"GROUP_JID{GROUP_JID}")
active_interactions = {}

wa_status_ref = db.reference('alfred_status/WhatsApp', app=app_1)

# Marca status online no Firebase
wa_status_ref.set({
    "status": "online",
    "last_update": datetime.now(timezone.utc).isoformat(),
    "image_name": "whatsapp-server:latest",
    "container_name": "alfred-whatsapp-agent"
})

def _get_user_info(pushNamer, participant, chat_id):
    """Extrai informações do usuário do objeto do WhatsApp."""
    short_chat_id = chat_id[:8] 
    participant_str = f"{participant}".replace('@s.whatsapp.net', '')
    pushNamer = f"{pushNamer}"
    
    return {
        "id": short_chat_id,
        "name": f"User {pushNamer}",
        "username": str(pushNamer),
        "platform": "WhatsApp"
    }

def _save_message_to_firebase(interaction_id, sender_type, content):
    """
    Salva uma mensagem no Firebase para uma interação específica.
    Args:
        interaction_id (str): O ID da interação (conversation).
        sender_type (str): 'user' ou 'Alfred'.
        content (str): O texto da mensagem.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    message_data = {
        "sender": sender_type,
        "content": content,
        "timestamp": timestamp
    }
    # Usa push() para criar um ID único para cada mensagem dentro da interação
    messages_db_ref.child(interaction_id).child('messages').push(message_data)
    print(f"Mensagem de '{sender_type}' salva na interação '{interaction_id}'")

def _update_interaction_status(interaction_id, new_status):
    """
    Atualiza o status de uma interação.
    Args:
        interaction_id (str): O ID da interação.
        new_status (str): Novo status ('pending', 'responded', 'resolved').
    """
    messages_db_ref.child(interaction_id).update({
        "status": new_status,
        "last_activity": datetime.now(timezone.utc).isoformat() # Opcional: para saber a última vez que a interação foi atualizada
    })
    print(f"Status da interação '{interaction_id}' atualizado para '{new_status}'")




@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    log.info(f"Mensagem recebida{data}")

    # Extraindo info do seu payload
    event = data.get("event")
    instance = data.get("instance")
    payload_data = data.get("data", {})

    jid = payload_data.get("key", {}).get("remoteJid")
    message_obj = payload_data.get("message", {})
    sender = payload_data.get("key", {}).get("participant")
    
    pushName = payload_data.get("pushName", {})

    # Aqui você identifica o texto
    texto_recebido = None
    if "conversation" in message_obj:
        texto_recebido = message_obj["conversation"]
    elif "extendedTextMessage" in message_obj:
        texto_recebido = message_obj["extendedTextMessage"].get("text")

    if texto_recebido:
        log.info(f"Texto recebido:{texto_recebido}")
        log.info(f"De:{jid}")

        chat_id = str(jid) 
        wats_message = texto_recebido
        print(f"chat_id: {chat_id}")
        print(f"WhatsApp_message: {wats_message}")
        user_info = _get_user_info(pushName, sender, chat_id) # <-- PEGA O DICIONÁRIO DE INFORMAÇÕES

        interaction_id = active_interactions.get(chat_id)

        if not interaction_id:
            new_interaction_ref = messages_db_ref.push({
                "user": user_info,  # <-- AGORA USA O DICIONÁRIO COMPLETO AQUI
                "status": "pending",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            interaction_id = new_interaction_ref.key
            active_interactions[chat_id] = interaction_id
            print(f"Nova interação criada: {interaction_id} para chat {chat_id}")
            _update_interaction_status(interaction_id, "pending")

        _save_message_to_firebase(interaction_id, "user", wats_message)
        # Processa com o Alfred
        Alfred_i = Alfred(app_1).Alfred
        resposta = await Alfred_i(texto_recebido)

        print(f"Resposta do Alfred: {resposta}")

        _save_message_to_firebase(interaction_id, "Alfred", resposta)


        url = f"{SERVER_URL}/message/sendText/{INSTANCE_NAME}"
        payload = {
            "number": jid,
            "options": {
                "delay": 500,                  # tempo em ms antes de enviar
                "presence": "composing",       # mostra "digitando..."
                "linkPreview": True,           # pré‑visualiza links
            },
            "textMessage": {
                "text": resposta
            }
        }
        headers = {
            "apikey": API_KEY,
            "Content-Type": "application/json"
        }
        resp = requests.post(url, json=payload, headers=headers)
        log.info(f"Resposta enviada. Status:{resp.status_code}")

        _update_interaction_status(interaction_id, "responded")


        # **Retorna algo para o Evolution não tentar reenviar / interpretar erro**
        return JSONResponse(content={"status": "ok"}, status_code=200)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5200, debug=True)

#     wa = WhatsAppEvolution(SERVER, INSTANCE, API_KEY, GROUP_JID)
#     wa.send_text_to_group()
