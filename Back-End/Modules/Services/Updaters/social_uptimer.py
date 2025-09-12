from datetime import datetime, timedelta, timezone
from AssistantSupport.ai import Alfred
import threading
from Keys.Firebase.FirebaseApp import init_firebase
from Modules.Loggers.logger import setup_logger 
from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus

from Modules.Services.Resolvers.user_identifier import resolve_user_identifier

from api import app


log = setup_logger("Services_update_interaction", "Services_update_interaction.log")


def start_uptime_updater(user_platform_id, category="Telegram"):
    """Agendador que atualiza o last_update a cada 60s."""
    def update_status():
        with app.app_context():
            user = resolve_user_identifier(user_platform_id)
            if user:
                agent = AgentStatus.query.filter_by(
                    platform=category, user_id=user.id
                ).first()
                if agent:
                    agent.last_update = datetime.now(timezone.utc)
                    db.session.commit()
                    log.info(f"[Uptime] last_update atualizado para {agent.last_update}")
        threading.Timer(60, update_status).start()

    update_status()
