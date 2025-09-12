
# Back-End\Modules\Services\update_interaction.py
from datetime import datetime, timedelta, timezone
from Modules.Loggers.logger import setup_logger 
from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus
from api import app

log = setup_logger("Services_update_interaction", "Services_update_interaction.log")

def _update_interaction_status_postgres(chat_id, new_status):
    """
    Atualiza o status da interação no PostgreSQL.
    Aqui, o 'status' pode ser salvo no model Message ou em outro model de controle de sessões se houver.
    """
    with app.app_context():
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
            db.session.commit()
            log.info(f"Status da interação '{chat_id}' atualizado para '{new_status}'")

