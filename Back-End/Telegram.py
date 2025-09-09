
# IMPORT SoftwareAI Libs 
from telegram import Bot
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),  'Keys', 'keys.env'))
os.chdir(os.path.join(os.path.dirname(__file__)))
import firebase_admin
from firebase_admin import db
from datetime import datetime, timedelta, timezone


from AssistantSupport.ai import Alfred
from Keys.Firebase.FirebaseApp import init_firebase
from Modules.Loggers.logger import setup_logger 
from Modules.Models.postgressSQL import db as db_postgress, User, Message, Config, AlfredFile, AgentStatus


log = setup_logger("Telegram", "Telegram.log")

app_1 = init_firebase()
telegram_status_ref = db.reference('alfred_status/Telegram', app=app_1)
messages_db_ref = db.reference('messages', app=app_1) 
configurations_db_ref = db.reference('configurations', app=app_1) 
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Knowledge')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    log.info(f"Created upload directory: {UPLOAD_FOLDER}")

class Telegram:
    """
    Essa classe faz a integracao oficial com a api do telegram,
    possibilitando envio e recebimento de mensagens em um canal especifico,

    - os agentes softwareai podem dar suporte a perguntas de usuarios e enviar imagens ao canal
    """
    def __init__(self, TOKEN, CHANNEL_ID):
        self.TelegramTOKEN = TOKEN
        self.CHANNEL_ID = CHANNEL_ID
        self.active_interactions = {}
        self.support_telegram_init = Bot(token=self.TelegramTOKEN)
        self.support_telegram = Application.builder().token(self.TelegramTOKEN).build()

        self.set_telegram_status_online()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Olá! Como posso ajudar você hoje?')

    async def reply_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_message = update.message
        chat_id = str(telegram_message.chat.id)

        user_info = self._get_user_info(telegram_message.from_user) # <-- PEGA O DICIONÁRIO DE INFORMAÇÕES
        user_text = telegram_message.text


        self._update_interaction_status_postgres(chat_id, "pending")

        self._save_message_to_postgres(chat_id, "user", user_text)
        Alfredclass = Alfred(app_1)
        self.Alfred = Alfredclass.Alfred
        Alfred_response = await self.Alfred(user_text)

        # if Deletemessage:
        #     try:
        #         chat_id = update.effective_chat.id
        #         message_id = update.effective_message.message_id
        #         await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        #     except Exception as e:
        #         print(f"Erro ao tentar deletar a mensagem: {e}")
        log.info(f"Resposta do Alfred: {Alfred_response}")

        self._save_message_to_postgres(chat_id, "user", Alfred_response)

        self._update_interaction_status_postgres(chat_id, "responded")

        await context.bot.send_message(chat_id=update.effective_chat.id, text=Alfred_response)

    async def handle_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lida com mensagens enviadas para um canal específico."""
        if update.message.chat_id == self.CHANNEL_ID:
            user_message = update.message.text
            user_id = update.message.from_user.id  
            telegram_message = update.message
            chat_id = str(telegram_message.chat.id)

            user_info = self._get_user_info(telegram_message.from_user) # <-- PEGA O DICIONÁRIO DE INFORMAÇÕES
            user_text = telegram_message.text

        
            self._update_interaction_status_postgres(chat_id, "pending")

            self._save_message_to_postgres(chat_id, "user", user_text, user_info)
            Alfredclass = Alfred(app_1)
            self.Alfred = Alfredclass.Alfred
            Alfred_response = await self.Alfred(user_text)

            # if Deletemessage:
            #     try:
            #         chat_id = update.effective_chat.id
            #         message_id = update.effective_message.message_id
            #         await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            #     except Exception as e:
            #         print(f"Erro ao tentar deletar a mensagem: {e}")
            log.info(f"Resposta do Alfred : {Alfred_response}")

            self._save_message_to_postgres(chat_id, "Alfred", Alfred_response, user_info)

            self._update_interaction_status_postgres(chat_id, "responded")

            # # Deletar mensagem do usuário
            # if Deletemessage:
            #     try:
            #         await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            #     except Exception as e:
            #         print(f"Erro ao tentar deletar a mensagem: {e}")

            # # Banir usuário
            # if BanUser:
            #     try:
            #         await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            #         print(f"Usuário {user_id} foi banido do canal {chat_id}.")
            #     except Exception as e:
            #         print(f"Erro ao tentar banir o usuário {user_id}: {e}")

            await context.bot.send_message(chat_id=chat_id, text=Alfred_response)
   
   
    def _save_message_to_postgres(self, chat_id, sender_type, content, user_info=None):
        """
        Salva uma mensagem no PostgreSQL para uma interação específica.
        Mantendo a mesma lógica do Firebase: cada chat tem uma 'session_id'.
        
        Args:
            chat_id (str): Identificador do chat (como o chat.id do Telegram).
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
                    email=f"{user_info['name']}@telegram.local",  # placeholder
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


    def set_telegram_status_online(self):
        agent = AgentStatus.query.filter_by(platform="Telegram").first()
        if not agent:
            agent = AgentStatus(
                platform="Telegram",
                status="online",
                last_update=datetime.now(timezone.utc),
                image_name="telegram-server:latest",
                container_name="alfred-telegram-agent"
            )
            db.session.add(agent)
        else:
            agent.status = "online"
            agent.last_update = datetime.now(timezone.utc)
            agent.image_name = "telegram-server:latest"
            agent.container_name = "alfred-telegram-agent"

        db.session.commit()
        
    def _get_user_info(self, telegram_user):
        """Extrai informações do usuário do objeto do Telegram."""
        return {
            "id": str(telegram_user.id),
            "name": telegram_user.full_name or telegram_user.first_name or f"User {telegram_user.id}",
            "username": telegram_user.username,
            "platform": "Telegram"
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
        messages_db_ref.child(interaction_id).child('messages').push(message_data)
        log.info(f"Mensagem de '{sender_type}' salva na interação '{interaction_id}'")

    def _update_interaction_status(self, interaction_id, new_status):
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
        log.info(f"Status da interação '{interaction_id}' atualizado para '{new_status}'")


    async def send_image_to_channel(self, image_path, caption=None):
        """
        Envia uma imagem para o canal.
        :param image_path: Caminho ou URL da imagem a ser enviada.
        :param caption: Texto opcional para incluir como legenda.
        """
        try:
            await self.support_telegram_init.send_photo(
                chat_id=self.CHANNEL_ID,
                photo=image_path,
                caption=caption
            )
            log.info(f"Imagem enviada para o canal {self.CHANNEL_ID}.")
        except Exception as e:
            log.info(f"Erro ao enviar imagem para o canal: {e}")



    def main_telegram(self):
        log.info("inicialized")
        self.support_telegram.add_handler(CommandHandler("start", self.start))
        self.support_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.reply_message))
        self.support_telegram.add_handler(MessageHandler(filters.TEXT & filters.Chat(self.CHANNEL_ID), self.handle_channel_message))
        self.support_telegram.run_polling()



if __name__ == '__main__':
    data = configurations_db_ref.get()
    TOKEN = data.get("botToken") 
    CHANNEL_ID =  data.get("channelId") 
    Telegram_instance = Telegram(TOKEN, CHANNEL_ID)
    Telegram_instance.main_telegram()