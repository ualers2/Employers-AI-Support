

import discord
import os
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
import threading
from datetime import datetime, timedelta, timezone

from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus
from api import app

from Modules.Services.Geters.user_info import _get_user_info
from Modules.Services.Savers.message import _save_message_to_postgres
from Modules.Services.Seters.status_online import set_status_online
from Modules.Services.Updaters.user_interaction import _update_interaction_status_postgres
from Modules.Services.Updaters.social_uptimer import start_uptime_updater
from Modules.Services.Resolvers.user_identifier import resolve_user_identifier
from Modules.Loggers.logger import setup_logger 

from Agents.AssistantSupport.ai import Alfred as alfredai


class Discord:
    """
    Essa classe faz a integracao oficial com a api do discord,
    possibilitando envio e recebimento de mensagens em um canal especifico,

    - os agentes softwareai podem dar suporte a perguntas de usuarios e enviar imagens ao canal
    """
    def __init__(self, CHANNEL_ID, discord_token, user_platform_id, app):
        self.intents = discord.Intents.default()
        self.intents.message_content = True 
        self.client_Discord = commands.Bot(command_prefix="!", intents=self.intents)
        self.CHANNEL_ID = CHANNEL_ID
        self.Discord_token = discord_token
        self.active_interactions = {}
        self.user_platform_id = user_platform_id
        set_status_online(self.user_platform_id, category="Discord")
        start_uptime_updater(self.user_platform_id, category="Discord")
        Alfredclass = alfredai(app)
        self.Alfred = Alfredclass.Alfred
                

        self.log = setup_logger("Discord", "Discord.log")

        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Knowledge')
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            self.log.info(f"Created upload directory: {UPLOAD_FOLDER}")


    def main_discord(self):
        @self.client_Discord.event
        async def on_ready():
            self.log.info(f'Bot conectado como {self.client_Discord.user}')

        @self.client_Discord.event
        async def on_message(message):
            if message.author == self.client_Discord.user:
                return

            chat_id = str(message.channel.id) 
            discord_message = message.content
            author_ = message.author
            self.log.info(f"chat_id: {chat_id}")
            self.log.info(f"author_: {author_}")
            self.log.info(f"discord_message: {discord_message}")
            user_info = _get_user_info(message, chat_id, telegram_user=None, category="Discord")
            

            _update_interaction_status_postgres(chat_id, "pending")

            _save_message_to_postgres(self.user_platform_id, chat_id, "user", discord_message, user_info)

            Alfred_response =  self.Alfred(discord_message, self.user_platform_id, chat_id, "discord")

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



            await message.channel.send(Alfred_response)

        @self.client_Discord.command()
        async def ping(ctx):
            await ctx.send("Pong!")

        Discord_tokenreplace = self.Discord_token.replace(" ", "")
        self.log.info(self.CHANNEL_ID)
        self.log.info(Discord_tokenreplace)
        self.log.info(self.Discord_token)
        self.log.info(f"{Discord_tokenreplace}")
        
        self.client_Discord.run(self.Discord_token)  # Discord


    async def send_image_to_discord(self, image_path, caption=None):
        """
        Envia uma imagem para o canal do Discord.
        :param image_path: Caminho ou URL da imagem a ser enviada.
        :param caption: Texto opcional para incluir como legenda.
        """
        try:
            channel = self.client.get_channel(self.CHANNEL_ID)
            await channel.send(content=caption, file=discord.File(image_path))
            self.log.info(f"Imagem enviada para o canal {self.CHANNEL_ID}.")
        except Exception as e:
            self.log.info(f"Erro ao enviar imagem para o canal: {e}")



if __name__ == '__main__':
    user_platform_id = os.getenv("USER_ID")
    CHANNEL_ID = os.getenv("discordChannelId")
    discord_token = os.getenv("discordBotToken")
    Discord_instance = Discord(CHANNEL_ID, discord_token, user_platform_id, app)
    Discord_instance.main_discord()