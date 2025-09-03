import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from fastapi import FastAPI, Request
# IMPORT SoftwareAI Alfred e Firebase
from Alfred import Alfred
from modules.Keys.Firebase.FirebaseApp import init_firebase
import firebase_admin
from firebase_admin import db
#########################################
from dotenv import load_dotenv, find_dotenv
from modules.Keys.Firebase.FirebaseApp import init_firebase
import firebase_admin
from firebase_admin import db
from datetime import datetime, timedelta, timezone


app_1 = init_firebase()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'modules', 'Keys', 'keys.env'))

class WhatsAppEvolution:
    """
    Classe para integração com a Evolution API do WhatsApp,
    permitindo envio e recebimento de mensagens em grupos,
    com suporte ao agente Alfred e registro no Firebase.
    """
    def __init__(self, server_url: str, instance_id: str, api_key: str, group_jid: str):
        self.server_url  = server_url.rstrip('/')
        self.instance_id = instance_id
        self.api_key     = api_key
        self.group_jid   = group_jid
        self.active_interactions = {}
                
        self.wa_status_ref = db.reference('alfred_status/WhatsApp', app=app_1)
        self.messages_db_ref = db.reference('messages', app=app_1) 
        self.configurations_db_ref = db.reference('configurations', app=app_1) 


        # Marca status online no Firebase
        self.wa_status_ref.set({
            "status": "online",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "instance": self.instance_id,
            "image_name": "whatsapp-server:latest",
            "container_name": "alfred-whatsapp-agent"
        })

    def _log_message(self, interaction_id: str, sender: str, content: str):
        """
        Salva registro de mensagem no Firebase.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        self.messages_db_ref.child(interaction_id).child('messages').push({
            "sender": sender,
            "content": content,
            "timestamp": timestamp
        })

    def _update_status(self, interaction_id: str, status: str):
        self.messages_db_ref.child(interaction_id).update({
            "status": status,
            "last_activity": datetime.now(timezone.utc).isoformat()
        })

    def list_groups(self) -> list:
        """
        Retorna lista de grupos em que a instância está participando.
        Exemplo de retorno: [{"jid": "123@g.us", "name": "Suporte"}, ...]
        """
        url = f"{self.server_url}/group/fetchAllGroups/{self.instance_id}"
        headers = { 'apikey': self.api_key }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _get_user_info(self, message, chat_id):
        """Extrai informações do usuário do objeto do Discord."""
        short_chat_id = chat_id[:8] 
        return {
            "id": short_chat_id,
            "name": f"User {message.author}",
            "username": str(message.author),
            "platform": "Discord"
        }

    def _save_message_to_firebase(self, interaction_id, sender_type, content):
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
        self.messages_db_ref.child(interaction_id).child('messages').push(message_data)
        print(f"Mensagem de '{sender_type}' salva na interação '{interaction_id}'")

    def _update_interaction_status(self, interaction_id, new_status):
        """
        Atualiza o status de uma interação.
        Args:
            interaction_id (str): O ID da interação.
            new_status (str): Novo status ('pending', 'responded', 'resolved').
        """
        self.messages_db_ref.child(interaction_id).update({
            "status": new_status,
            "last_activity": datetime.now(timezone.utc).isoformat() # Opcional: para saber a última vez que a interação foi atualizada
        })
        print(f"Status da interação '{interaction_id}' atualizado para '{new_status}'")


    async def send_text_to_group(self, text: str, mentions_everyone: bool=False) -> dict:
        """
        Envia texto para o grupo configurado (self.group_jid).
        Retorna a resposta da API.
        """
        url = f"{self.server_url}/message/sendText/{self.instance_id}"

        payload = {
            "number": self.group_jid,
            "options": {
                "delay": 500,                  # tempo em ms antes de enviar
                "presence": "composing",       # mostra "digitando..."
                "linkPreview": True,           # pré‑visualiza links
            },
            "textMessage": {
                "text": text
            }
        }
        if mentions_everyone:
            payload["mentionsEveryOne"] = True

        headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(response.json())

        return response.json()
