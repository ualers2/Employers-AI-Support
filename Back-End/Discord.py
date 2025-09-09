

import discord
import os
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
import firebase_admin
from firebase_admin import db
from datetime import datetime, timedelta, timezone

from AssistantSupport.ai import Alfred
from Keys.Firebase.FirebaseApp import init_firebase
from Modules.Loggers.logger import setup_logger 
from Modules.Models.postgressSQL import db as db_postgress, User, Message, Config, AlfredFile, AgentStatus


log = setup_logger("Discord", "Discord.log")
app_1 = init_firebase()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'Keys', 'keys.env'))
configurations_db_ref = db.reference('configurations', app=app_1) 
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Knowledge')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    log.info(f"Created upload directory: {UPLOAD_FOLDER}")
class Discord:
    """
    Essa classe faz a integracao oficial com a api do discord,
    possibilitando envio e recebimento de mensagens em um canal especifico,

    - os agentes softwareai podem dar suporte a perguntas de usuarios e enviar imagens ao canal
    """
    def __init__(self, CHANNEL_ID, discord_token):
        self.intents = discord.Intents.default()
        self.intents.message_content = True 
        self.client_Discord = commands.Bot(command_prefix="!", intents=self.intents)
        self.CHANNEL_ID = CHANNEL_ID
        self.Discord_token = discord_token
        self.active_interactions = {}

        self.messages_db_ref = db.reference('messages', app=app_1) 

        self.set_discord_status_online()

    def main_discord(self):
        @self.client_Discord.event
        async def on_ready():
            log.info(f'Bot conectado como {self.client_Discord.user}')

        @self.client_Discord.event
        async def on_message(message):
            if message.author == self.client_Discord.user:
                return

            chat_id = str(message.channel.id) 
            discord_message = message.content
            author_ = message.author
            log.info(f"chat_id: {chat_id}")
            log.info(f"author_: {author_}")
            log.info(f"discord_message: {discord_message}")
            user_info = self._get_user_info(message, chat_id)

            self._update_interaction_status_postgres(chat_id, "pending")

            self._save_message_to_postgres(chat_id, "user", discord_message, user_info)

            Alfredclass = Alfred(app_1)
            self.Alfred = Alfredclass.Alfred
            Alfred_response = await self.Alfred(discord_message)

            # if Deletemessage:
            #     try:
            #         chat_id = update.effective_chat.id
            #         message_id = update.effective_message.message_id
            #         await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            #     except Exception as e:
            #         print(f"Erro ao tentar deletar a mensagem: {e}")
            log.info(f"Resposta do Alfred: {Alfred_response}")

            self._save_message_to_postgres(chat_id, "Alfred", Alfred_response, user_info)
            self._update_interaction_status_postgres(chat_id, "responded")



            await message.channel.send(Alfred_response)

        @self.client_Discord.command()
        async def ping(ctx):
            await ctx.send("Pong!")

        Discord_tokenreplace = self.Discord_token.replace(" ", "")
        log.info(self.CHANNEL_ID)
        log.info(Discord_tokenreplace)
        log.info(self.Discord_token)
        log.info(f"{Discord_tokenreplace}")
        
        self.client_Discord.run(self.Discord_token)  # Discord

    def set_discord_status_online(self):
        agent = AgentStatus.query.filter_by(platform="Discord").first()
        if not agent:
            agent = AgentStatus(
                platform="Discord",
                status="online",
                last_update=datetime.now(timezone.utc),
                image_name="discord-server:latest",
                container_name="alfred-discord-agent"
            )
            db.session.add(agent)
        else:
            agent.status = "online"
            agent.last_update = datetime.now(timezone.utc)
            agent.image_name = "discord-server:latest"
            agent.container_name = "alfred-discord-agent"

        db.session.commit()
    def _get_user_info(self, message, chat_id):
        """Extrai informações do usuário do objeto do Discord."""
        short_chat_id = chat_id[:8] 
        return {
            "id": short_chat_id,
            "name": f"User {message.author}",
            "username": str(message.author),
            "platform": "Discord"
        }
    
    def _save_message_to_postgres(self, chat_id, sender_type, content, user_info=None):
        """
        Salva uma mensagem no PostgreSQL para uma interação específica.
        Mantendo a mesma lógica do Firebase: cada chat tem uma 'session_id'.
        
        Args:
            chat_id (str): Identificador do chat (como o channel.id do Discord).
            sender_type (str): 'user' ou 'Alfred'.
            content (str): Texto da mensagem.
            user_info (dict, opcional): Informações do usuário. Necessário se sender_type == 'user'.
        """
        timestamp = datetime.now(timezone.utc)

        user_obj = None
        if sender_type == "user" and user_info:
            # Checa se o usuário já existe
            user_obj = User.query.filter_by(platform_id=chat_id).first()
            if not user_obj:
                user_obj = User(
                    email=f"{user_info['username']}@discord.local",  # placeholder
                    name=user_info["name"],
                    platform_id=chat_id
                )
                db_postgress.session.add(user_obj)
                db_postgress.session.commit()

        msg = Message(
            session_id=chat_id,
            user_id=user_obj.id if user_obj else None,
            role=sender_type,
            content=content,
            created_at=timestamp
        )
        db_postgress.session.add(msg)
        db_postgress.session.commit()
        log.info(f"Mensagem de '{sender_type}' salva no Postgres para chat '{chat_id}'")


    def _update_interaction_status_postgres(self, chat_id, new_status):
        """
        Atualiza o status da interação no PostgreSQL.
        Aqui, o 'status' pode ser salvo no model Message ou em outro model de controle de sessões se houver.
        """
        last_msg = (
            Message.query.filter_by(session_id=chat_id)
            .order_by(Message.created_at.desc())
            .first()
        )
        if last_msg:
            if not last_msg.meta:
                last_msg.meta = {}
            last_msg.meta["status"] = new_status
            last_msg.meta["last_activity"] = datetime.now(timezone.utc).isoformat()
            db_postgress.session.commit()
            log.info(f"Status da interação '{chat_id}' atualizado para '{new_status}'")

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
        log.info(f"Mensagem de '{sender_type}' salva na interação '{interaction_id}'")

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
        log.info(f"Status da interação '{interaction_id}' atualizado para '{new_status}'")



    async def send_image_to_discord(self, image_path, caption=None):
        """
        Envia uma imagem para o canal do Discord.
        :param image_path: Caminho ou URL da imagem a ser enviada.
        :param caption: Texto opcional para incluir como legenda.
        """
        try:
            channel = self.client.get_channel(self.CHANNEL_ID)
            await channel.send(content=caption, file=discord.File(image_path))
            log.info(f"Imagem enviada para o canal {self.CHANNEL_ID}.")
        except Exception as e:
            log.info(f"Erro ao enviar imagem para o canal: {e}")



if __name__ == '__main__':
    data = configurations_db_ref.get()
    CHANNEL_ID = data.get("discordChannelId") # , os.getenv("CHANNEL_ID_discord")
    discord_token =  data.get("discordBotToken") # , os.getenv("discord_token")
    Discord_instance = Discord(CHANNEL_ID, discord_token)
    Discord_instance.main_discord()