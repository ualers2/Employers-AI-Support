
# Back-End\Modules\Services\save_message.py
import os
from datetime import datetime, timedelta, timezone
from Modules.Loggers.logger import setup_logger 
from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus
from Modules.FileServer.download_ import download_


log = setup_logger("Services_user_file_paths", "user_file_paths.log")


def get_user_file_paths(app,
                        user_identifier, 
                        UPLOAD_URL_VIDEOMANAGER,
                        project_name,
                        USER_ID_FOR_TEST):
    try:
        with app.app_context():
            if isinstance(user_identifier, int) or str(user_identifier).isdigit():
                user = User.query.get(int(user_identifier))
            else:
                user = User.query.filter_by(email=user_identifier).first()

            if not user:
                log.info(f"Usuário '{user_identifier}' não encontrado.")
                return []

            files = AlfredFile.query.filter_by(uploaded_by_user_id=user.id).all()
            if not files:
                log.info(f"Nenhum arquivo encontrado para usuário {user.id} ({user.email})")
                return []

            local_paths = []
            for f in files:
                file_id  = f.file_id
                unique_filename = f.unique_filename
                save_path = os.path.join(os.path.dirname(__file__), "../", "../", "../", "Knowledge", f"{unique_filename}")
                local_path = download_(UPLOAD_URL_VIDEOMANAGER, save_path, project_name, file_id, USER_ID_FOR_TEST)
                if local_path and os.path.exists(local_path):
                    local_paths.append(local_path)
                else:
                    log.warning(f"Arquivo não encontrado no disco: {local_path}")

            log.info(f"Retornados {len(local_paths)} arquivos para o usuário {user.id} ({user.email})")
            return local_paths

    except Exception as e:
        log.error(f"Erro ao buscar arquivos do usuário {user_identifier}: {e}", exc_info=True)
        return []

