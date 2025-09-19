# Back-End\WhatsApp.py
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from Modules.Loggers.logger import setup_logger 

from Agents.AssistantSupport.ai import Alfred as alfredai
from Modules.Models.postgressSQL import db as db_postgress, User, Message, Config, AlfredFile, AgentStatus
from Modules.Services.Geters.user_info import _get_user_info
from Modules.Services.Savers.message import _save_message_to_postgres
from Modules.Services.Updaters.user_interaction import _update_interaction_status_postgres
from Modules.Services.Seters.status_online import set_status_online
from api import app as app_flask


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'Keys', 'keys.env'))

app = FastAPI()
log = setup_logger("whatsapp_webhook", "webhook.log")
active_interactions = {}


user_platform_id = os.getenv('USER_ID')
SERVER_URL = os.getenv("waServerUrl") 
INSTANCE_NAME =  os.getenv("waInstanceId")
API_KEY = os.getenv("waApiKey") 
GROUP_JID =  os.getenv("waSupportGroupJid")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Knowledge')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    log.info(f"Created upload directory: {UPLOAD_FOLDER}")


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    log.info(f"Mensagem recebida{data}")
    event = data.get("event")
    instance = data.get("instance")
    payload_data = data.get("data", {})
    jid = payload_data.get("key", {}).get("remoteJid")
    message_obj = payload_data.get("message", {})
    sender = payload_data.get("key", {}).get("participant")
    pushName = payload_data.get("pushName", {})

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
        log.info(f"chat_id: {chat_id}")
        log.info(f"WhatsApp_message: {wats_message}")
        user_info = _get_user_info(chat_id, pushNamer=pushName, category='WhatsApp') 

        _update_interaction_status_postgres(chat_id, "pending")

        _save_message_to_postgres(user_platform_id, chat_id, "user", wats_message, user_info)

        Alfred_i = alfredai(app_flask).Alfred
        resposta = await Alfred_i(wats_message, user_platform_id, chat_id, "whatsapp")

        log.info(f"Resposta do Alfred: {resposta}")

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

        _save_message_to_postgres(user_platform_id, chat_id, "assistant", resposta, user_info)

        _update_interaction_status_postgres(chat_id, "responded")

        return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == "__main__":
    set_status_online(user_platform_id=user_platform_id, category='WhatsApp')
    app.run(host="0.0.0.0", port=5200, debug=True)
