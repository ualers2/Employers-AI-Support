
# Back-End\Modules\Services\save_message.py
from datetime import datetime, timedelta, timezone
from Modules.Loggers.logger import setup_logger 
from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus
from api import app

log = setup_logger("Services_save_message", "Services_save_message.log")

def _save_message_to_postgres(user_platform_id, chat_id, sender_type, content, user_info=None):
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
    with app.app_context():
        user_obj = None
        # if sender_type == "user" and user_info:
        # Checa se o usuário já existe
        user_obj = User.query.filter_by(email=user_platform_id).first()
        if not user_obj:
            if not user_info.get("name", ''):
                name = user_info.get("username", '')
            else:
                name = user_info.get("name", '')
            user_obj = User(
                email=user_platform_id,
                name=name,
                platform_id=chat_id
            )
            db.session.add(user_obj)
            db.session.commit()

        msg = Message(
            session_id=chat_id,
            user_id=user_obj.id if user_obj else None,
            role=sender_type,
            content=content,
            created_at=timestamp
        )
        db.session.add(msg)
        db.session.commit()
        log.info(f"Mensagem de '{sender_type}' salva no Postgres para chat '{chat_id}'")

