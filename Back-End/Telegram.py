
# Back-End\Telegram.py
from telegram import Bot
from dotenv import load_dotenv
import threading
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),  'Keys', 'keys.env'))
os.chdir(os.path.join(os.path.dirname(__file__)))


from Agents.AssistantSupport.ai import Alfred as alfredai

from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus
from api import app


from Modules.Services.Geters.user_info import _get_user_info
from Modules.Services.Savers.message import _save_message_to_postgres
from Modules.Services.Seters.status_online import set_status_online
from Modules.Services.Updaters.user_interaction import _update_interaction_status_postgres
from Modules.Services.Updaters.social_uptimer import start_uptime_updater
from Modules.Services.Resolvers.user_identifier import resolve_user_identifier
from Modules.Loggers.logger import setup_logger 



class Telegram:
    """
    Essa classe faz a integracao oficial com a api do telegram,
    possibilitando envio e recebimento de mensagens em um canal especifico,

    - os agentes softwareai podem dar suporte a perguntas de usuarios e enviar imagens ao canal
    """
    def __init__(self, TOKEN, CHANNEL_ID, user_platform_id, app):
        self.TelegramTOKEN = TOKEN
        self.CHANNEL_ID = CHANNEL_ID
        self.active_interactions = {}
        self.support_telegram_init = Bot(token=self.TelegramTOKEN)
        self.support_telegram = Application.builder().token(self.TelegramTOKEN).build()
        self.user_platform_id = user_platform_id
        set_status_online(self.user_platform_id, category="Telegram")
        start_uptime_updater(self.user_platform_id, category="Telegram")
        Alfredclass = alfredai(app)
        self.Alfred = Alfredclass.Alfred
                
        self.log = setup_logger("Telegram", "Telegram.log", logging.DEBUG)

        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Knowledge')
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            self.log.info(f"Created upload directory: {UPLOAD_FOLDER}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Olá! Como posso ajudar você hoje?')

    async def reply_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_message = update.message
        chat_id = str(telegram_message.chat.id)

        user_info = _get_user_info(telegram_message.from_user, chat_id, telegram_user=telegram_message.from_user, category="Telegram")
        
        user_text = telegram_message.text


        self.log.info(f"chat_id {chat_id}")
        _update_interaction_status_postgres(chat_id, "pending")

        _save_message_to_postgres(self.user_platform_id, chat_id, "user", user_text, user_info)

        Alfred_response = self.Alfred(user_text, self.user_platform_id, chat_id, "telegram")

        # if Deletemessage:
        #     try:
        #         chat_id = update.effective_chat.id
        #         message_id = update.effective_message.message_id
        #         await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        #     except Exception as e:
        #         print(f"Erro ao tentar deletar a mensagem: {e}")
        self.log.info(f"Resposta do Alfred: {Alfred_response}")

        _save_message_to_postgres(self.user_platform_id, chat_id, "assistant", Alfred_response, user_info)

        _update_interaction_status_postgres(chat_id, "responded")

        await context.bot.send_message(chat_id=update.effective_chat.id, text=Alfred_response)

    async def handle_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lida com mensagens enviadas para um canal específico."""
        self.CHANNEL_ID = int(self.CHANNEL_ID)

        if update.message.chat_id == self.CHANNEL_ID:
            user_message = update.message.text
            user_id = update.message.from_user.id  
            telegram_message = update.message
            chat_id = str(telegram_message.chat.id)

            user_info = _get_user_info(telegram_message.from_user, chat_id, telegram_user=telegram_message.from_user, category="Telegram")
            user_text = telegram_message.text

            self.log.info(f"chat_id {chat_id}")
            _update_interaction_status_postgres(chat_id, "pending")

            _save_message_to_postgres(self.user_platform_id, chat_id, "user", user_text, user_info)

            Alfred_response = await self.Alfred(user_text, self.user_platform_id, chat_id, "telegram")

            # if Deletemessage:
            #     try:
            #         chat_id = update.effective_chat.id
            #         message_id = update.effective_message.message_id
            #         await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            #     except Exception as e:
            #         print(f"Erro ao tentar deletar a mensagem: {e}")
            self.log.info(f"Resposta do Alfred : {Alfred_response}")

            _save_message_to_postgres(self.user_platform_id, chat_id, "assistant", Alfred_response, user_info)

            _update_interaction_status_postgres(chat_id, "responded")

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
            self.log.info(f"Imagem enviada para o canal {self.CHANNEL_ID}.")
        except Exception as e:
            self.log.info(f"Erro ao enviar imagem para o canal: {e}")



    def main_telegram(self):
        self.log.info("inicialized")
        self.support_telegram.add_handler(CommandHandler("start", self.start))
        self.support_telegram.add_handler(MessageHandler(filters.TEXT & filters.Chat(self.CHANNEL_ID), self.handle_channel_message))
        self.support_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.reply_message))

        self.support_telegram.run_polling()



if __name__ == '__main__':
    # load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),'Keys', 'keys.env'))

    user_platform_id = os.getenv("USER_ID") 
    TOKEN = os.getenv("botToken") 
    CHANNEL_ID =  os.getenv("channelId") 
    Telegram_instance = Telegram(TOKEN, CHANNEL_ID, user_platform_id, app)
    Telegram_instance.main_telegram()