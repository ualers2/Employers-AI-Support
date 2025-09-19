from datetime import datetime, timedelta, timezone
from Modules.Loggers.logger import setup_logger 
from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus

from Modules.Services.Resolvers.user_identifier import resolve_user_identifier

from api import app

def set_status_online(user_platform_id, category="Discord"):
    with app.app_context():

        user = resolve_user_identifier(user_platform_id)
        if not user:
            return "Usuário não encontrado."
        
        numeric_user_id = user.id
        if category == "Discord":

            agent = AgentStatus.query.filter_by(platform="Discord", user_id=numeric_user_id).first()
            if not agent:
                agent = AgentStatus(
                    name="Alfred Discord Agent",
                    area="Suporte Ao Cliente",
                    tasks=['Responder usuários', 'Abrir tickets', 'Coletar feedback'],
                    workingHours='24/7',
                    platform="Discord",
                    status="online",
                    last_update=datetime.now(timezone.utc),
                    image_name="mediacutsstudio/discord-server:latest",
                    container_name="alfred-discord-agent",
                    user_id=numeric_user_id
                )
                db.session.add(agent)
            else:
                agent.status = "online"
                agent.last_update = datetime.now(timezone.utc)
        
        elif category == "Telegram":

            agent = AgentStatus.query.filter_by(platform="Telegram", user_id=numeric_user_id).first()
            if not agent:
                agent = AgentStatus(
                    name="Alfred Telegram Agent",
                    area="Suporte Ao Cliente",
                    tasks=['Responder usuários', 'Abrir tickets', 'Coletar feedback'],
                    workingHours='24/7',
                    platform="Telegram",
                    status="online",
                    last_update=datetime.now(timezone.utc),
                    image_name="mediacutsstudio/telegram-server:latest",
                    container_name="alfred-telegram-agent",
                    user_id=numeric_user_id
                )
                db.session.add(agent)
            else:
                agent.status = "online"
                agent.last_update = datetime.now(timezone.utc)
        
        elif category == "WhatsApp":

            agent = AgentStatus.query.filter_by(platform="WhatsApp", user_id=numeric_user_id).first()
            if not agent:
                agent = AgentStatus(
                    name="Alfred WhatsApp Agent",
                    area="Suporte Ao Cliente",
                    tasks=['Responder usuários', 'Abrir tickets', 'Coletar feedback'],
                    workingHours='24/7',
                    platform="WhatsApp",
                    status="online",
                    last_update=datetime.now(timezone.utc),
                    image_name="mediacutsstudio/whatsapp-server:latest",
                    container_name="whatsapp-telegram-agent",
                    user_id=numeric_user_id
                )
                db.session.add(agent)
            else:
                agent.status = "online"
                agent.last_update = datetime.now(timezone.utc)
        

        db.session.commit()
