# Back-End\api.py

import os
import logging
import uuid
import json
import asyncio
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from typing import List, Dict
from firebase_admin import db
from datetime import datetime, timedelta, timezone
from docker import DockerClient, errors
import docker 
import asyncio
import logging
from flask import request, jsonify
from typing import Dict, Any, Optional
from datetime import datetime
import time
from sqlalchemy import desc, func


from ClienteChat.ai import CustomerChatAgent
from Keys.Firebase.FirebaseApp import init_firebase
from Modules.Models.postgressSQL import db as db_postgress, User, Message, Config, AlfredFile, AgentStatus

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),'Keys', 'keys.env'))

try:
    client = DockerClient(base_url='unix://var/run/docker.sock')
except docker.errors.DockerException as e:
    logger.warning(f"Não foi possível conectar ao Docker: {e}")
    client = None 

app_1 = init_firebase()
db_ref = db.reference('configurations', app=app_1) 
users_db_ref = db.reference('users', app=app_1)
messages_db_ref = db.reference('messages', app=app_1) 
telegram_status_ref = db.reference('alfred_status/Telegram', app=app_1)     
discord_status_ref = db.reference('alfred_status/Discord', app=app_1)     
WhatsApp_status_ref = db.reference('alfred_status/WhatsApp', app=app_1)    
alfred_files_metadata_ref = db.reference('alfred_knowledge_metadata', app=app_1)

UPLOAD_URL_VIDEOMANAGER = os.getenv("UPLOAD_URL")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Knowledge')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Created upload directory: {UPLOAD_FOLDER}")
METADATA_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'alfred_files_metadata.json')
last_alfred_heartbeat = datetime.now(timezone.utc)

# Configuração do banco PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@meu_postgres:5432/meubanco"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db_postgress.init_app(app)

with app.app_context():
    db_postgress.create_all()  # cria tabelas se não existirem


# Endpoint para criar login (cadastro)
@app.route("/api/create-login", methods=["POST"])
def create_login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Usuário já existe"}), 400

    new_user = User(email=email)
    new_user.set_password(password)

    db_postgress.session.add(new_user)
    db_postgress.session.commit()

    return jsonify({"message": "Usuário criado com sucesso"}), 201


# Endpoint para login
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciais inválidas"}), 401

    return jsonify({"message": f"Bem-vindo, {user.email}!"}), 200


@app.route("/api/chat-assistant", methods=["POST"])
def chat_assistant():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "JSON payload required"}), 400

        user_msg = data.get("message", "").strip()
        if not user_msg:
            return jsonify({"success": False, "error": "Message field is required"}), 400

        user_context = data.get("user_context", {})
        conversation_history = data.get("conversation_history", [])
        user_id = user_context.get("user_id")  # pode ser None
        session_id = data.get("session_id") or str(uuid.uuid4())  # garante um id
        enable_analytics = data.get("enable_analytics", True)
        model = data.get("model", "gpt-5-nano")

        # --- IDENTIFICAR USUÁRIO ---
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "error": "Usuário não encontrado"}), 401

        # --- SALVAR MENSAGEM DO USUÁRIO ---
        user_message = Message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=user_msg
        )
        db_postgress.session.add(user_message)
        db_postgress.session.commit()

        enriched_context = _enrich_user_context(user_context, request)

        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "storage")
        result = asyncio.run(CustomerChatAgent(
            content_user=user_msg,
            UPLOAD_FOLDER=UPLOAD_FOLDER,
            user_context=enriched_context,
            conversation_history=conversation_history,
            model=model,
            UPLOAD_URL=UPLOAD_URL_VIDEOMANAGER,
            USER_ID=str(user_id),
            enable_analytics=enable_analytics
        ))

        if result["success"]:
            agent_output = result["response"].content

            # --- SALVAR MENSAGEM DO ASSISTENTE ---
            assistant_message = Message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=agent_output
            )
            db_postgress.session.add(assistant_message)
            db_postgress.session.commit()

            response_data = _format_successful_response(result, session_id)
        else:
            agent_output = f"[ERRO] {result.get('error')}"
            assistant_message = Message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=agent_output
            )
            db_postgress.session.add(assistant_message)
            db_postgress.session.commit()

            response_data = _format_error_response(result, user_msg, session_id)

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Unexpected error in chat_assistant: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "Ocorreu um erro interno. Nossa equipe foi notificada."
        }), 500
    

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'GET':
        try:
            configs = Config.query.all()
            default = {
                "botConfig": {},
                "moderationConfig": {},
                "alfredConfig": {}
            }
            for c in configs:
                default[c.key] = c.value if isinstance(c.value, dict) else {}
            return jsonify(default), 200
        except Exception as e:
            logger.exception("Erro em get_configurations")
            return jsonify({"error": "Erro interno ao buscar configurações"}), 500

    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            for key, value in data.items():
                config = Config.query.filter_by(key=key).first()
                if config:
                    config.value = value
                else:
                    config = Config(key=key, value=value)
                    db_postgress.session.add(config)
            db_postgress.session.commit()
            return jsonify({"message": "Configurações salvas com sucesso!"}), 200
        except Exception as e:
            logger.exception(f"Error saving configurations: {e}")
            return jsonify({"error": "Erro ao salvar configurações."}), 500
        

@app.route('/api/alfred-files/upload', methods=['POST'])
def upload_alfred_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo fornecido."}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "Arquivo inválido."}), 400

    channel_id = request.form.get('channelId')
    caption = request.form.get('caption')

    allowed_extensions = {'md', 'txt', 'pdf', 'docx', 'csv', 'json'}
    file_extension = file.filename.rsplit('.', 1)[-1].lower()
    if file_extension not in allowed_extensions:
        return jsonify({"error": f"Formato de arquivo não permitido."}), 400

    try:
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        file_stats = os.stat(file_path)
        file_size_bytes = file_stats.st_size
        last_modified_timestamp = datetime.fromtimestamp(file_stats.st_mtime)

        # Salvar no PostgreSQL
        alfred_file = AlfredFile(
            unique_filename=unique_filename,
            original_filename=file.filename,
            channel_id=channel_id,
            caption=caption,
            size_bytes=file_size_bytes,
            last_modified_local=last_modified_timestamp,
            local_path=file_path,
            url_download=f"/api/alfred-files/download/{unique_filename}",
            url_content=f"/api/alfred-files/{unique_filename}/content"
        )
        db_postgress.session.add(alfred_file)
        db_postgress.session.commit()

        return jsonify({
            "message": "Arquivo carregado com sucesso.",
            "fileId": unique_filename,
            "fileName": file.filename,
            "size": format_bytes(file_size_bytes),
            "lastModified": last_modified_timestamp.isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"Erro no upload do arquivo: {e}")
        return jsonify({"error": "Erro no servidor ao processar o upload."}), 500

@app.route('/api/alfred-files', methods=['GET'])
def list_alfred_files():
    """
    Lista todos os arquivos Alfred com seus metadados do PostgreSQL.
    """
    try:
        files_list = []

        alfred_files = AlfredFile.query.all()
        for af in alfred_files:
            if not os.path.exists(af.local_path):
                logger.warning(f"Arquivo '{af.unique_filename}' existe no DB mas não no disco. Pulando.")
                continue

            file_stats = os.stat(af.local_path)
            last_modified_dt = datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc)

            files_list.append({
                "id": af.unique_filename,
                "name": af.original_filename,
                "type": get_file_type(af.original_filename),
                "size": format_bytes(file_stats.st_size),
                "lastModified": last_modified_dt.isoformat(),
                "url": af.url_download,
                "localPath": af.local_path
            })

        return jsonify(files_list), 200

    except Exception as e:
        logger.exception("Erro ao listar arquivos Alfred")
        return jsonify({"error": "Erro interno ao buscar arquivos."}), 500
    
@app.route('/api/alfred-files/<string:fileId>/content', methods=['PUT'])
def update_alfred_file_content(fileId):
    """
    Atualiza o conteúdo de um arquivo Alfred no disco e os metadados no PostgreSQL.
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({"error": "'content' é obrigatório."}), 400

        new_content = data['content']
        if not isinstance(new_content, str):
            return jsonify({"error": "'content' deve ser uma string."}), 400

        # Busca o arquivo no PostgreSQL
        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId).first()
        if not alfred_file:
            return jsonify({"error": "Arquivo não encontrado."}), 404

        file_path = alfred_file.local_path
        if not os.path.exists(file_path):
            return jsonify({"error": "Arquivo não existe no disco."}), 404

        # Atualiza conteúdo local
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        file_stats = os.stat(file_path)
        last_modified_timestamp = datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc)

        # Atualiza metadados no PostgreSQL
        alfred_file.size_bytes = file_stats.st_size
        alfred_file.last_modified_local = last_modified_timestamp
        db_postgress.session.commit()

        return jsonify({
            "message": "Conteúdo atualizado com sucesso.",
            "fileId": fileId,
            "lastModified": last_modified_timestamp.isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"Erro ao atualizar conteúdo do arquivo {fileId}: {e}")
        return jsonify({"error": "Erro interno ao atualizar o arquivo."}), 500
    
@app.route('/api/alfred-files/<string:fileId>/content', methods=['GET'])
def get_alfred_file_content(fileId):
    """
    Retorna o conteúdo de um arquivo Alfred e seus metadados do PostgreSQL.
    """
    try:
        # Busca no PostgreSQL
        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId).first()
        if not alfred_file:
            return jsonify({"error": "Arquivo não encontrado."}), 404

        file_path = alfred_file.local_path
        if not os.path.exists(file_path):
            return jsonify({"error": "Arquivo não existe no disco."}), 404

        # Somente extensões de texto podem ser lidas
        file_extension = alfred_file.original_filename.rsplit('.', 1)[1].lower() if '.' in alfred_file.original_filename else ''
        allowed_readable_extensions = {'md', 'txt', 'csv', 'json'}

        if file_extension not in allowed_readable_extensions:
            return jsonify({"error": "Visualização de conteúdo não suportada para este tipo de arquivo."}), 400

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        last_modified_timestamp = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)

        return jsonify({
            "id": fileId,
            "name": alfred_file.original_filename,
            "content": content,
            "lastModified": last_modified_timestamp.isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"Erro ao buscar conteúdo do arquivo {fileId}: {e}")
        return jsonify({"error": "Erro interno ao buscar o conteúdo do arquivo."}), 500
    
@app.route('/api/alfred-files/<string:fileId>/download', methods=['GET'])
def download_alfred_file(fileId):
    """
    Permite o download de um arquivo Alfred usando metadados do PostgreSQL.
    """
    try:
        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId).first()
        if not alfred_file:
            return jsonify({"error": "Arquivo não encontrado."}), 404

        file_path = alfred_file.local_path
        if not os.path.exists(file_path):
            return jsonify({"error": "Arquivo não encontrado no disco."}), 404

        filename_on_disk = os.path.basename(file_path)

        return send_from_directory(
            UPLOAD_FOLDER,
            filename_on_disk,
            as_attachment=True,
            download_name=alfred_file.original_filename
        )

    except Exception as e:
        logger.exception(f"Erro ao baixar arquivo {fileId}: {e}")
        return jsonify({"error": "Erro interno ao tentar baixar o arquivo."}), 500
    
@app.route('/api/alfred-files/<string:fileId>', methods=['DELETE'])
def delete_alfred_file(fileId):
    """
    Remove um arquivo Alfred do disco e seus metadados do PostgreSQL.
    """
    try:
        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId).first()
        file_path = alfred_file.local_path if alfred_file else os.path.join(UPLOAD_FOLDER, fileId)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Arquivo '{fileId}' excluído do disco.")

        if alfred_file:
            db_postgress.session.delete(alfred_file)
            db_postgress.session.commit()
            logger.info(f"Metadados do arquivo '{fileId}' removidos do PostgreSQL.")

        return jsonify({"message": "Arquivo excluído com sucesso."}), 200

    except Exception as e:
        logger.exception(f"Erro ao excluir arquivo {fileId}: {e}")
        return jsonify({"error": "Erro interno ao excluir o arquivo."}), 500


@app.route('/api/messages/recent', methods=['GET'])
def list_recent_messages():
    limit = request.args.get('limit', default=10, type=int)
    status_filter = request.args.get('status')
    after_id = request.args.get('after_id')

    # Buscar últimas mensagens por session_id
    query = db.session.query(
        Message.session_id,
        func.max(Message.created_at).label('last_timestamp'),
        func.max(Message.id).label('last_message_id')
    ).group_by(Message.session_id)

    if status_filter:
        # Aqui depende se você tem coluna de status na Message ou User
        pass

    query = query.order_by(desc('last_timestamp')).limit(limit)
    results = query.all()

    interactions = []
    for row in results:
        last_message = Message.query.get(row.last_message_id)
        user = last_message.user
        interactions.append({
            "id": row.session_id,
            "user": user.email if user else "Unknown User",
            "userId": user.id if user else None,
            "message": last_message.content,
            "timestamp": last_message.created_at.isoformat(),
            "status": "responded"  # Exemplo, você pode mapear de outra forma
        })

    return jsonify(interactions), 200

@app.route('/api/messages/<string:session_id>', methods=['GET'])
def get_interaction_details(session_id):
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    if not messages:
        return jsonify({"error": "Interação/Ticket não encontrado."}), 404

    user = messages[0].user if messages else None

    formatted_messages = [
        {
            "messageId": m.id,
            "sender": m.role,
            "timestamp": m.created_at.isoformat(),
            "content": m.content
        }
        for m in messages
    ]

    return jsonify({
        "interactionId": session_id,
        "user": {
            "name": user.email if user else "Unknown",
            "id": user.id if user else None,
        },
        "status": "responded",  # Você pode criar campo de status se quiser
        "messages": formatted_messages
    }), 200

@app.route('/api/users', methods=['GET'])
def list_users():
    search_term = request.args.get('searchTerm', '').lower()
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)

    query = User.query

    if search_term:
        query = query.filter(
            (func.lower(User.email).like(f"%{search_term}%"))
        )

    query = query.order_by(User.email).offset(offset)
    if limit:
        query = query.limit(limit)

    users = query.all()
    return jsonify([
        {
            "id": u.id,
            "name": u.email,
            "status": "active"  # Se quiser, pode adicionar campo status
        }
        for u in users
    ]), 200
@app.route('/api/users/<int:user_id>/ban', methods=['POST'])
def ban_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404

    # Aqui você precisa adicionar coluna `status` na model User
    user.status = 'banned'
    db.session.commit()
    return jsonify({"message": "Usuário banido com sucesso.", "userId": user.id, "status": user.status})


@app.route('/api/users/<int:user_id>/unban', methods=['POST'])
def unban_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404

    user.status = 'active'
    db.session.commit()
    return jsonify({"message": "Usuário desbanido com sucesso.", "userId": user.id, "status": user.status})

@app.route('/api/metrics/realtime', methods=['GET'])
def get_realtime_metrics():
    try:
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        fifteen_minutes_ago = now - timedelta(minutes=15)

        # 1) messages in last hour
        messages_in_last_hour = Message.query.filter(Message.created_at >= one_hour_ago).count()

        # 2) online users (last_seen within 15 minutes)
        online_users_count = User.query.filter(User.last_seen != None).filter(User.last_seen >= fifteen_minutes_ago).count()

        # 3) average response time (pair user -> assistant (Alfred) within same session)
        total_response_time = 0.0
        response_count = 0

        # Query messages ordered by session_id and created_at to group them in Python
        msgs = Message.query.order_by(Message.session_id, Message.created_at).all()
        from collections import defaultdict
        sessions = defaultdict(list)
        for m in msgs:
            sessions[m.session_id].append(m)

        for session_id, mlist in sessions.items():
            # mlist already sorted by created_at due to query order_by
            for i, m in enumerate(mlist):
                if m.role == 'user':
                    user_msg_time = m.created_at.replace(tzinfo=timezone.utc) if m.created_at.tzinfo is None else m.created_at
                    # find next assistant message after this user message
                    for subsequent in mlist[i+1:]:
                        if subsequent.role == 'assistant':
                            alfred_msg_time = subsequent.created_at.replace(tzinfo=timezone.utc) if subsequent.created_at.tzinfo is None else subsequent.created_at
                            if alfred_msg_time > user_msg_time:
                                time_diff = (alfred_msg_time - user_msg_time).total_seconds()
                                if time_diff >= 0:
                                    total_response_time += time_diff
                                    response_count += 1
                                break

        average_response_time = total_response_time / response_count if response_count > 0 else 0.0

        metrics = {
            "messagesPerHour": messages_in_last_hour,
            "onlineUsers": online_users_count,
            "averageResponseTime": round(average_response_time, 2)
        }

        logger.info(f"Real-time metrics calculated: {metrics}")
        return jsonify(metrics), 200

    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao calcular ou buscar as métricas."}), 500

@app.route('/api/activities', methods=['GET'])
def list_activities():
    try:
        # Query params
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', default=0, type=int)
        activity_type_filter = request.args.get('type')
        status_filter = request.args.get('status')
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        search_term = request.args.get('searchTerm', '').lower()

        # validation
        if offset < 0:
            return jsonify({"error": "O parâmetro 'offset' deve ser um número inteiro não negativo."}), 400
        if limit is not None and limit <= 0:
            return jsonify({"error": "O parâmetro 'limit' deve ser um número inteiro positivo."}), 400

        valid_types = {'message', 'ban', 'unban', 'file', 'response', 'error', 'info', None}
        if activity_type_filter and activity_type_filter not in valid_types:
            return jsonify({"error": f"O tipo de atividade '{activity_type_filter}' é inválido. Valores possíveis: {', '.join(t for t in valid_types if t)}."}), 400

        valid_statuses = {'success', 'warning', 'info', 'error', None}
        if status_filter and status_filter not in valid_statuses:
            return jsonify({"error": f"O status de atividade '{status_filter}' é inválido. Valores possíveis: {', '.join(s for s in valid_statuses if s)}."}), 400

        start_date = None
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({"error": "Formato de 'startDate' inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)."}), 400

        end_date = None
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({"error": "Formato de 'endDate' inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)."}), 400

        if start_date and end_date and start_date > end_date:
            return jsonify({"error": "'startDate' não pode ser posterior a 'endDate'."}), 400

        all_activities = []
        activity_id_counter = 0

        # --- 1. Activities from Messages ---
        # We'll load messages grouped by session_id and create activity per message (user/assistant)
        msgs = Message.query.order_by(Message.session_id, Message.created_at).all()
        from collections import defaultdict
        sessions = defaultdict(list)
        for m in msgs:
            sessions[m.session_id].append(m)

        for session_id, mlist in sessions.items():
            # resolve user name (try first message user)
            session_user_name = None
            session_user_platform_id = None
            for m in mlist:
                if m.user_id:
                    u = User.query.get(m.user_id)
                    if u:
                        session_user_name = u.name or u.email
                        session_user_platform_id = u.platform_id
                        break

            for idx, m in enumerate(mlist):
                activity_id_counter += 1
                timestamp = m.created_at
                # normalize tz
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                if m.role == 'user':
                    activity = {
                        "id": f"msg_{session_id}_{idx}",
                        "timestamp": timestamp.isoformat(),
                        "status": "success",
                        "type": "message",
                        "user": session_user_name or "Unknown User",
                        "action": "Enviou mensagem",
                        "details": (m.content[:100] + "...") if len(m.content) > 100 else m.content
                    }
                elif m.role == 'assistant':
                    activity = {
                        "id": f"resp_{session_id}_{idx}",
                        "timestamp": timestamp.isoformat(),
                        "status": "success",
                        "type": "response",
                        "user": "Alfred (Bot)",
                        "action": "Respondeu à mensagem",
                        "details": (m.content[:100] + "...") if len(m.content) > 100 else m.content
                    }
                else:
                    # Ignora roles desconhecidos
                    continue

                all_activities.append(activity)

        # --- 2. Activities from Users (ban/unban) ---
        banned_users = User.query.filter(User.status == 'banned').all()
        for u in banned_users:
            activity_id_counter += 1
            timestamp = u.last_seen or datetime.now(timezone.utc)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            all_activities.append({
                "id": f"ban_{u.id}_{activity_id_counter}",
                "type": "ban",
                "user": u.name or u.email or f"user_{u.id}",
                "action": "Usuário Banido",
                "details": f"Motivo: '{u.ban_reason or 'N/A'}'. Duração: '{u.ban_duration or 'N/A'}'.",
                "timestamp": timestamp.isoformat(),
                "status": "warning"
            })

        # --- 3. Activities from Alfred Files (uploads) ---
        files = AlfredFile.query.order_by(AlfredFile.uploaded_at.desc()).all()
        for f in files:
            activity_id_counter += 1
            ts = f.uploaded_at or datetime.now(timezone.utc)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            all_activities.append({
                "id": f"file_upload_{f.id}_{activity_id_counter}",
                "type": "file",
                "user": f.uploaded_by_user_id and (User.query.get(f.uploaded_by_user_id).name or User.query.get(f.uploaded_by_user_id).email) or "Sistema (Admin)",
                "action": "Arquivo Carregado",
                "details": f"Arquivo '{f.original_filename}' ({f.unique_filename}) carregado.",
                "timestamp": ts.isoformat(),
                "status": "success"
            })

        # --- 4. Apply Filters (date, type, status, search) ---
        filtered_activities = []
        for activity in all_activities:
            activity_timestamp = datetime.fromisoformat(activity['timestamp'])
            if activity_timestamp.tzinfo is None:
                activity_timestamp = activity_timestamp.replace(tzinfo=timezone.utc)

            if start_date and activity_timestamp < start_date:
                continue
            if end_date and activity_timestamp > end_date:
                continue
            if activity_type_filter and activity['type'] != activity_type_filter:
                continue
            if status_filter and activity.get('status') != status_filter:
                continue

            if search_term:
                user_match = search_term in (activity.get('user') or '').lower()
                action_match = search_term in (activity.get('action') or '').lower()
                details_match = search_term in (activity.get('details') or '').lower()
                if not (user_match or action_match or details_match):
                    continue

            filtered_activities.append(activity)

        # sort descending by timestamp
        filtered_activities.sort(key=lambda x: datetime.fromisoformat(x['timestamp']), reverse=True)

        # pagination
        total_activities = len(filtered_activities)
        paginated = filtered_activities[offset:]
        if limit is not None:
            paginated = paginated[:limit]

        logger.info(f"Retrieved {len(paginated)} activities (total filtered: {total_activities}) with filters: {request.args}.")
        return jsonify({"total": total_activities, "activities": paginated}), 200

    except ValueError as ve:
        logger.error(f"Bad Request for activities: {ve}", exc_info=True)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error listing activities: {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao buscar o log de atividades."}), 500

@app.route('/api/activities', methods=['DELETE'])
def clear_activities():
    try:
        before_date_str = request.args.get('beforeDate')
        status_filter = request.args.get('status')

        deleted_count = 0

        before_date = None
        if before_date_str:
            try:
                before_date = datetime.fromisoformat(before_date_str)
                if before_date.tzinfo is None:
                    before_date = before_date.replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({"error": "Formato de 'beforeDate' inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)."}), 400

        valid_statuses = {'success', 'warning', 'info', 'error', None}
        if status_filter and status_filter not in valid_statuses:
            return jsonify({"error": f"O status de atividade '{status_filter}' é inválido para exclusão. Valores possíveis: {', '.join(s for s in valid_statuses if s)}."}), 400

        # --- Delete message interactions whose earliest message is before before_date ---
        if before_date:
            # Encontrar session_ids com earliest message < before_date
            session_earliest = db.session.query(
                Message.session_id,
                func.min(Message.created_at).label('earliest')
            ).group_by(Message.session_id).having(func.min(Message.created_at) < before_date).all()

            session_ids_to_delete = [row.session_id for row in session_earliest]
            if session_ids_to_delete:
                # delete messages
                del_q = Message.__table__.delete().where(Message.session_id.in_(session_ids_to_delete))
                res = db.session.execute(del_q)
                deleted_count += res.rowcount if hasattr(res, 'rowcount') else 0
                db.session.commit()
                logger.info(f"Deleted {len(session_ids_to_delete)} interactions (sessions) from messages.")

            # --- Delete AlfredFile metadata older than before_date ---
            files_to_delete = AlfredFile.query.filter(AlfredFile.uploaded_at < before_date).all()
            for f in files_to_delete:
                # opcional: deletar arquivo no disco se desejar:
                # try:
                #     if os.path.exists(f.local_path):
                #         os.remove(f.local_path)
                # except Exception as ex:
                #     logger.warning(f"Erro ao remover arquivo local {f.local_path}: {ex}")
                db.session.delete(f)
                deleted_count += 1
            db.session.commit()

        # Note: Status-based deletion not implemented com precisão porque 'status'
        # não é um campo direto nas mensagens; precisa de model Activity ou marcação na Message.
        # Por enquanto, beforeDate é o principal filtro.

        logger.info(f"Activity log clear operation completed. deletedCount={deleted_count}")
        return jsonify({"message": "Log de atividades limpo com sucesso.", "deletedCount": deleted_count}), 200

    except Exception as e:
        logger.error(f"Error clearing activities: {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao limpar o log de atividades."}), 500


@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Handles GET requests to /api/dashboard/stats.
    Returns aggregated metrics for the dashboard cards.
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Define periods for comparison: last 24 hours and previous 24 hours
        today_24h_ago = now - timedelta(hours=24)
        yesterday_24h_ago = today_24h_ago - timedelta(hours=24)

        total_messages = 0
        active_users_today = set()
        active_users_yesterday = set()
        alfred_responses_today = 0
        alfred_responses_yesterday = 0
        messages_today = 0
        messages_yesterday = 0

        # Fetch all messages
        all_interactions_raw = messages_db_ref.get()

        if isinstance(all_interactions_raw, dict):
            for interaction_id, interaction_data in all_interactions_raw.items():
                if isinstance(interaction_data, dict) and 'messages' in interaction_data:
                    user_id = interaction_data.get('user', {}).get('id')
                    
                    messages_in_interaction = []
                    if isinstance(interaction_data['messages'], dict):
                        messages_in_interaction = list(interaction_data['messages'].values())
                    elif isinstance(interaction_data['messages'], list):
                        messages_in_interaction = [msg for msg in interaction_data['messages'] if msg is not None]

                    for msg in messages_in_interaction:
                        if isinstance(msg, dict) and 'timestamp' in msg and 'sender' in msg:
                            total_messages += 1
                            try:
                                msg_timestamp = datetime.fromisoformat(msg['timestamp'])
                                if msg_timestamp.tzinfo is None:
                                    msg_timestamp = msg_timestamp.replace(tzinfo=timezone.utc)

                                if msg_timestamp >= today_24h_ago:
                                    if user_id:
                                        active_users_today.add(user_id)
                                    messages_today += 1
                                    if msg['sender'] == 'Alfred':
                                        alfred_responses_today += 1
                                elif msg_timestamp >= yesterday_24h_ago: # Messages from the previous 24h period
                                    if user_id:
                                        active_users_yesterday.add(user_id)
                                    messages_yesterday += 1
                                    if msg['sender'] == 'Alfred':
                                        alfred_responses_yesterday += 1

                            except ValueError as ve:
                                logger.warning(f"Invalid timestamp format in message for stats: {msg.get('timestamp', 'N/A')} - {ve}")



        # --- BUSCA 'filesManaged' DO FIREBASE ---
        files_managed = 0
        try:
            # Pega todos os metadados de arquivos do Firebase
            all_files_metadata = alfred_files_metadata_ref.get()
            if all_files_metadata:
                # Se houver dados, conta o número de entradas (arquivos)
                # all_files_metadata será um dicionário onde as chaves são os nomes dos arquivos
                files_managed = len(all_files_metadata)
        except Exception as e:
            logger.error(f"Erro ao buscar metadados de arquivos do Firebase: {e}", exc_info=True)
            files_managed = 0 # Define como 0 em caso de erro na busca
        # --- FIM DA BUSCA DO FIREBASE ---

        # Calculate percentages
        def calculate_percentage_change(current, previous):
            if previous == 0:
                return current * 100 if current > 0 else 0 # If previous was 0 and current is >0, it's a huge increase
            change = ((current - previous) / previous) * 100
            return round(change, 2)

        total_messages_change_percentage = calculate_percentage_change(messages_today, messages_yesterday)
        active_users_change_percentage = calculate_percentage_change(len(active_users_today), len(active_users_yesterday))
        alfred_responses_change_percentage = calculate_percentage_change(alfred_responses_today, alfred_responses_yesterday)

        stats = {
            "totalMessages": total_messages,
            "activeUsers": len(active_users_today),
            "alfredResponses": alfred_responses_today, # Display current period's responses
            "filesManaged": files_managed,
            "totalMessagesChangePercentage": total_messages_change_percentage,
            "activeUsersChangePercentage": active_users_change_percentage,
            "alfredResponsesChangePercentage": alfred_responses_change_percentage
        }

        logger.info(f"Dashboard statistics calculated: {stats}")
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {e}")
        return jsonify({"error": "Erro no servidor ao buscar as estatísticas do dashboard."}), 500

@app.route('/api/alfred/status', methods=['GET'])
def get_alfred_status():
    """
    Handles GET requests to /api/alfred/status.
    Verifies the connectivity and operational status of the Alfred agent,
    with primary focus on the Telegram integration status from Firebase.
    """
    global last_alfred_heartbeat # Keep if you intend to simulate/update it elsewhere

    current_status = "offline"
    current_message = "Alfred está offline ou inacessível."
    details = {
        "telegramApiConnected": False,
        "DiscordApiConnected": False,
        "WhatsAppApiConnected": False,
        "databaseConnected": False,
        "lastHeartbeat": last_alfred_heartbeat.isoformat() # Still provide heartbeat info
    }

    current_status_Discord = "offline"
    current_message_Discord = "(Discord) Offline."
    current_status = "offline"
    current_message = "(Telegram) Offline."
    current_status_WhatsApp = "offline"
    current_message_WhatsApp = "(WhatsApp) Offline."
    try:
        # 1. Check Firebase Database Connectivity (general check)
        try:
            # Try to read a small, non-sensitive piece of data (e.g., config)
            # A simple read from a known path is sufficient for connectivity check
            test_val = db_ref.child('configurations').get() # Assuming 'configurations' path exists
            details["databaseConnected"] = True
            logger.info("Firebase database connection successful.")
        except Exception as e:
            logger.error(f"Firebase database connection test failed: {e}")


        # Only proceed to check Telegram status if the database itself is connected
        if details["databaseConnected"]:
            Discord_data = discord_status_ref.get()
            logger.info(f"Discord_data: {Discord_data}")

            Telegram_data = telegram_status_ref.get()
            logger.info(f"Telegram_data: {Telegram_data}")

            WhatsApp_data = WhatsApp_status_ref.get()
            logger.info(f"WhatsApp_data: {WhatsApp_data}")

            if Discord_data and isinstance(Discord_data, dict):
                Discord_bot_status = Discord_data.get("status")
                Discord_last_update_str = Discord_data.get("last_update")


                details["DiscordApiConnected"] = (Discord_bot_status == "online")
                
                if Discord_last_update_str:
                    try:
                        Discord_last_update_dt = datetime.fromisoformat(Discord_last_update_str)
                        if Discord_last_update_dt.tzinfo is None:
                            Discord_last_update_dt = Discord_last_update_dt.replace(tzinfo=timezone.utc)
                        details["lastHeartbeat"] = Discord_last_update_dt.isoformat() # Use Telegram's last_update as heartbeat

                        # Determine status based on Telegram's reported status and last update time
                        if Discord_bot_status == "online" and (datetime.now(timezone.utc) - Discord_last_update_dt) < timedelta(days=1):
                            current_status_Discord = "online"
                            current_message_Discord = "(Discord) Conectado."
                        elif Discord_bot_status == "online": # Online but old heartbeat
                            current_status_Discord = "degraded"
                            current_message_Discord = "Alfred (Discord) online, mas o último update é antigo. Pode haver problemas de comunicação."
                        else: # Status is not "online"
                            current_status_Discord = "offline"
                            current_message_Discord = f"Alfred (Discord) está {Discord_bot_status.lower()}."
                    except ValueError as ve:
                        logger.warning(f"Invalid timestamp format in Telegram status: {Discord_last_update_str} - {ve}")
                        current_status_Discord = "degraded"
                        current_message_Discord = "Alfred (Discord) online, mas com timestamp inválido. Verifique logs."
                else:
                    # Discord_ status exists but no last_update (unlikely if 'status' is present)
                    if Discord_bot_status == "online":
                        current_status_Discord = "degraded"
                        current_message_Discord = "Alfred (Discord) online, mas sem registro de último update."
                    else:
                        current_status_Discord = "offline"
                        current_message_Discord = f"Alfred (Discord) está {Discord_bot_status.lower()}."

            if Telegram_data and isinstance(Telegram_data, dict):
                telegram_bot_status = Telegram_data.get("status")
                telegram_last_update_str = Telegram_data.get("last_update")


                details["telegramApiConnected"] = (telegram_bot_status == "online")
                
                if telegram_last_update_str:
                    try:
                        telegram_last_update_dt = datetime.fromisoformat(telegram_last_update_str)
                        if telegram_last_update_dt.tzinfo is None:
                            telegram_last_update_dt = telegram_last_update_dt.replace(tzinfo=timezone.utc)
                        details["lastHeartbeat"] = telegram_last_update_dt.isoformat() # Use Telegram's last_update as heartbeat

                        # Determine status based on Telegram's reported status and last update time
                        if telegram_bot_status == "online" and (datetime.now(timezone.utc) - telegram_last_update_dt) < timedelta(days=1):
                            current_status = "online"
                            current_message = "(Telegram) Conectado."
                        elif telegram_bot_status == "online": # Online but old heartbeat
                            current_status = "degraded"
                            current_message = "Alfred (Telegram) online, mas o último update é antigo. Pode haver problemas de comunicação."
                        else: # Status is not "online"
                            current_status = "offline"
                            current_message = f"Alfred (Telegram) está {telegram_bot_status.lower()}."
                    except ValueError as ve:
                        logger.warning(f"Invalid timestamp format in Telegram status: {telegram_last_update_str} - {ve}")
                        current_status = "degraded"
                        current_message = "Alfred (Telegram) online, mas com timestamp inválido. Verifique logs."
                else:
                    # Telegram status exists but no last_update (unlikely if 'status' is present)
                    if telegram_bot_status == "online":
                        current_status = "degraded"
                        current_message = "Alfred (Telegram) online, mas sem registro de último update."
                    else:
                        current_status = "offline"
                        current_message = f"Alfred (Telegram) está {telegram_bot_status.lower()}."

            if WhatsApp_data and isinstance(WhatsApp_data, dict):
                WhatsApp_status = WhatsApp_data.get("status")
                WhatsApp_last_update_str = WhatsApp_data.get("last_update")
                details["WhatsAppApiConnected"] = (WhatsApp_status == "online")
                if WhatsApp_last_update_str:
                    try:
                        WhatsApp_last_update_dt = datetime.fromisoformat(WhatsApp_last_update_str)
                        if WhatsApp_last_update_dt.tzinfo is None:
                            WhatsApp_last_update_dt = WhatsApp_last_update_dt.replace(tzinfo=timezone.utc)
                        details["lastHeartbeat"] = WhatsApp_last_update_dt.isoformat() 

                        # Determine status based on WhatsApp's reported status and last update time
                        if WhatsApp_status == "online" and (datetime.now(timezone.utc) - WhatsApp_last_update_dt) < timedelta(days=1):
                            current_status_WhatsApp = "online"
                            current_message_WhatsApp = "(WhatsApp) Conectado."
                        elif WhatsApp_status == "online": # Online but old heartbeat
                            current_status_WhatsApp = "degraded"
                            current_message_WhatsApp = "Alfred (WhatsApp) online, mas o último update é antigo. Pode haver problemas de comunicação."
                        else: # Status is not "online"
                            current_status_WhatsApp = "offline"
                            current_message_WhatsApp = f"Alfred (WhatsApp) está {telegram_bot_status.lower()}."
                    except ValueError as ve:
                        logger.warning(f"Invalid timestamp format in WhatsApp status: {telegram_last_update_str} - {ve}")
                        current_status_WhatsApp = "degraded"
                        current_message_WhatsApp = "Alfred (WhatsApp) online, mas com timestamp inválido. Verifique logs."
                else:
                    # WhatsApp status exists but no last_update (unlikely if 'status' is present)
                    if WhatsApp_status == "online":
                        current_status_WhatsApp = "degraded"
                        current_message_WhatsApp = "Alfred (WhatsApp) online, mas sem registro de último update."
                    else:
                        current_status_WhatsApp = "offline"
                        current_message_WhatsApp = f"Alfred (WhatsApp) está {telegram_bot_status.lower()}."



        else:
            current_status = "offline"
            current_message = "Alfred está offline. Falha na conexão com o banco de dados Firebase."

    except Exception as e:
        logger.error(f"Internal server error when checking Alfred status: {e}")
        current_status = "error"
        current_message = "Erro interno do servidor ao verificar o status do Alfred."

    current_message_final = current_message + current_message_Discord + current_message_WhatsApp
    logger.info(f"Alfred status checked: {current_status}, Message: {current_message}, Details: {details}")
    return jsonify({
        "status": current_status,
        "message": current_message_final,
        "details": details
    }), 200

@app.route('/api/agents/initialize', methods=['POST'], strict_slashes=False)
def initialize_agent():
    """
    Inicializa um novo agente (Discord, Telegram ou whatsapp) buscando a image_name
    diretamente das referências de status no Firebase.
    Requer: platform (discord/telegram/whatsapp). agentConfigId não é mais necessário.
    """
    data = request.get_json()
    platform = data.get('platform')
    logger.info(data)
    if not platform:
        return jsonify({"message": "Platform é obrigatório."}), 400

    if platform not in ['discord', 'telegram', 'whatsapp']:
        return jsonify({"message": "Plataforma inválida. Use 'discord' ou 'telegram'."}), 400

    try:
        container_name = f"alfred-{platform}-agent"

        success, message = _start_docker_container(container_name)

        if success:
            return jsonify({"message": message, "status": "initializing"}), 200
        else:
            return jsonify({"message": message, "status": "failed"}), 500

    except Exception as e:
        print(f"Erro ao inicializar agente {platform}: {e}")
        return jsonify({"message": f"Erro interno ao inicializar agente: {e}"}), 500

@app.route('/api/agents/<platform>/reset', methods=['POST'])
def reset_agent(platform):
    """
    Reinicia o contêiner Docker de um agente específico.
    Busca a image_name diretamente das referências de status no Firebase.
    """

    container_name = f"alfred-{platform}-agent"

    try:
        # Para e remove o container existente
        stop_success, stop_message = _stop_docker_container(container_name)
        # remove_success, remove_message = _remove_docker_container(container_name)

        if not stop_success and "não encontrado" not in stop_message:
            return jsonify({"message": f"Erro ao tentar reiniciar (parar): {stop_message}"}), 500
  
        # Inicia um novo container
        start_success, start_message = _start_docker_container(container_name)
        if start_success:
            return jsonify({"message": f"Agente {platform} reiniciado com sucesso. {start_message}", "status": "restarting"}), 200
        else:
            return jsonify({"message": f"Falha ao reiniciar agente {platform}: {start_message}", "status": "failed"}), 500

    except Exception as e:
        print(f"Erro ao reiniciar agente {platform}: {e}")
        return jsonify({"message": f"Erro interno ao reiniciar agente: {e}"}), 500

@app.route('/api/agents/<platform>/pause', methods=['POST'])
def pause_agent(platform):
    """
    Pausa ou despausa o contêiner Docker de um agente específico.
    """

    container_name = f"alfred-{platform}-agent"

    try:
        if not client:
            raise Exception("Docker client não está disponível.")
        container = client.containers.get(container_name)
        if container.status == 'paused':
            container.unpause()
            return jsonify({"message": f"Agente {platform} despausado com sucesso.", "status": "running"}), 200
        else:
            container.pause()
            return jsonify({"message": f"Agente {platform} pausado com sucesso.", "status": "paused"}), 200
    except docker.errors.NotFound:
        return jsonify({"message": f"Container '{container_name}' não encontrado para pausar/despausar."}), 404
    except docker.errors.APIError as e:
        return jsonify({"message": f"Erro na API Docker ao pausar/despausar {container_name}: {e}"}), 500
    except Exception as e:
        print(f"Erro ao pausar/despausar agente {platform}: {e}")
        return jsonify({"message": f"Erro interno ao pausar/despausar agente: {e}"}), 500

@app.route('/api/agents/<platform>/delete', methods=['DELETE'])
def delete_agent(platform):
    """
    Deleta o contêiner Docker de um agente específico.
    """
    container_name = f"alfred-{platform}-agent"

    success, message = _remove_docker_container(container_name)

    if success:
        return jsonify({"message": message, "status": "deleted"}), 200
    else:
        # Se não for encontrado, ainda é um "sucesso" em termos de que não está mais lá
        if "não encontrado" in message:
            return jsonify({"message": f"Container '{container_name}' já não existe ou não foi encontrado. {message}", "status": "not_found"}), 200
        return jsonify({"message": message, "status": "failed"}), 500

@app.route('/callback')
def oauth_callback():
    # 1) Pega o código que o provedor OAuth enviou
    code = request.args.get('code')
    if not code:
        return "Erro: nenhum código recebido", 400

    # 2) Troca o code por token
    token_response = trocar_code_por_token(code)
    access_token = token_response.get('access_token')

    # 3) Armazene/processar o access_token como precisar
    #    (por exemplo, salvar na sessão ou no banco)

    return "Autenticação concluída com sucesso! Feche esta janela."

def trocar_code_por_token(code):
    import requests
    data = {
        'client_id':      os.getenv("ClientID_discord"),
        'client_secret':  os.getenv("ClientSecret_discord"),
        'grant_type':     'authorization_code',
        'code':           code,
        'redirect_uri':   'http://localhost:8080/callback'
    }
    resp = requests.post('https://discord.com/api/oauth2/token', data=data)
    return resp.json()

def _enrich_user_context(user_context: Dict[str, Any], request_obj) -> Dict[str, Any]:
    """Enriquece o contexto do usuário com informações da requisição"""
    
    enriched = user_context.copy()
    
    # Adiciona timestamp
    enriched["timestamp"] = datetime.utcnow().isoformat()
    
    # Informações da requisição (se necessário para analytics)
    enriched["request_info"] = {
        "user_agent": request_obj.headers.get("User-Agent", ""),
        "ip": request_obj.environ.get("HTTP_X_FORWARDED_FOR", request_obj.remote_addr),
        "referer": request_obj.headers.get("Referer", "")
    }
    
    # Define user_id se não fornecido
    if not enriched.get("user_id"):
        enriched["user_id"] = f"anonymous_{hash(enriched['request_info']['ip']) % 10000}"
    
    # Inferências básicas se dados não fornecidos
    if not enriched.get("user_type"):
        enriched["user_type"] = "prospect"  # Default para visitantes da landing page
    
    return enriched

def _format_successful_response(result: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    """Formata resposta de sucesso com dados estruturados"""
    
    response = result["response"]
    analytics = result.get("analytics")
    
    # Resposta base
    response_data = {
        "success": True,
        "reply": response.content,
        "metadata": {
            "conversation_type": response.conversation_type,
            "user_intent": response.user_intent,
            "response_tone": response.response_tone,
            "escalation_needed": response.escalation_needed,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    # Adiciona session_id se fornecido
    if session_id:
        response_data["session_id"] = session_id
    
    # Próximos passos sugeridos
    if response.next_steps:
        response_data["suggested_actions"] = response.next_steps
    
    # Sugestões de follow-up
    if response.follow_up_suggestions:
        response_data["follow_up_suggestions"] = response.follow_up_suggestions
    
    # Analytics (se habilitado e disponível)
    if analytics:
        response_data["analytics"] = {
            "satisfaction_score": analytics.user_satisfaction_score,
            "key_topics": analytics.key_topics,
            "conversation_summary": analytics.conversation_summary
        }
        
        # Oportunidades de marketing (apenas para uso interno)
        if analytics.marketing_opportunities:
            response_data["internal"] = {
                "marketing_opportunities": analytics.marketing_opportunities
            }
    
    # Indicadores para o frontend
    response_data["ui_hints"] = {
        "show_escalation_option": response.escalation_needed,
        "highlight_cta": response.conversation_type == "marketing",
        "show_satisfaction_survey": response.conversation_type == "support"
    }
    
    return response_data

def _format_error_response(result: Dict[str, Any], user_msg: str, session_id: Optional[str]) -> Dict[str, Any]:
    """Formata resposta de erro com fallback amigável"""
    
    response_data = {
        "success": False,
        "reply": "Desculpe, estou enfrentando dificuldades técnicas no momento. "
                "Nossa equipe foi notificada e entrará em contato em breve. "
                "Para urgências, você pode usar nosso chat de suporte direto.",
        "error_type": "processing_error",
        "timestamp": datetime.utcnow().isoformat(),
        "suggested_actions": [
            "Tente reformular sua pergunta",
            "Acesse nossa documentação",
            "Entre em contato com suporte direto"
        ]
    }
    
    if session_id:
        response_data["session_id"] = session_id
    
    # Se temos uma resposta de fallback do agente, use ela
    if "response" in result and result["response"]:
        response_data["reply"] = result["response"].content
        response_data["suggested_actions"] = result["response"].next_steps or response_data["suggested_actions"]
    
    return response_data

def save_message_to_firebase(session_id, role, content):
    """
    Salva uma mensagem no Firebase Realtime Database.
    Estrutura: /conversations/<session_id>/messages
    """
    ref = db.reference(f"conversations/{session_id}/messages", app=app_1)
    new_msg = {
        "role": role,            # "user" ou "assistant"
        "content": content,
        "timestamp": int(time.time())
    }
    ref.push(new_msg)

def _start_docker_container(container_name: str):
    """
    Reinicia um container Docker pelo nome. Se não existir, retorna erro.
    """
    if not client:
        raise Exception("Docker client não está disponível.")
    try:
        container = client.containers.get(container_name)
        container.start()
        return True, f"Container '{container_name}' reiniciado com sucesso!"
    except errors.NotFound:
        return False, f"Container '{container_name}' não encontrado."
    except errors.APIError as e:
        return False, f"Erro na API Docker ao reiniciar '{container_name}': {e}"
    except Exception as e:
        return False, f"Erro inesperado ao reiniciar '{container_name}': {e}"
    
def _stop_docker_container(container_name: str):
    if not client:
        raise Exception("Docker client não está disponível.")
    try:
        container = client.containers.get(container_name)
        container.stop()
        return True, f"Container '{container_name}' parado com sucesso."
    except docker.errors.NotFound:
        return False, f"Container '{container_name}' não encontrado."
    except docker.errors.APIError as e:
        return False, f"Erro na API Docker ao parar {container_name}: {e}"
    except Exception as e:
        return False, f"Erro inesperado ao parar Docker container {container_name}: {e}"

def _remove_docker_container(container_name: str):
    if not client:
        raise Exception("Docker client não está disponível.")
    try:
        container = client.containers.get(container_name)
        container.remove()
        return True, f"Container '{container_name}' removido com sucesso."
    except docker.errors.NotFound:
        return False, f"Container '{container_name}' não encontrado."
    except docker.errors.APIError as e:
        return False, f"Erro na API Docker ao remover {container_name}: {e}"
    except Exception as e:
        return False, f"Erro inesperado ao remover Docker container {container_name}: {e}"

def _get_docker_container_status(container_name: str):
    if not client:
        return "offline", "Docker client não está disponível."
    try:
        container = client.containers.get(container_name)
        return container.status, f"Status: {container.status}"
    except docker.errors.NotFound:
        return "offline", "Container não existe."
    except Exception as e:
        return "error", f"Erro ao obter status: {e}"

def format_bytes(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in {'md', 'txt'}:
        return "document"
    elif ext in {'pdf'}:
        return "pdf"
    elif ext in {'docx'}:
        return "word"
    elif ext in {'csv', 'json'}:
        return "data"
    else:
        return "other"

def get_configurations():
    try:
        raw = db_ref.get() or {}
        default = {
            "botConfig": {
                "botToken": "",
                "channelId": "",
                "discordBotToken": "",
                "discordChannelId": "",
                "waServerUrl": '',
                "waInstanceId": '',
                "waApiKey": '',
                "waSupportGroupJid": '',
            },
            "moderationConfig": {
                "autoModeration": False,
                "aiModeration": False,
                "aiModerationModel": "ominilatest",
                "deleteSpam": False,
                "banThreshold": 3,
            },
            "alfredConfig": {
                "alfredName": "Alfred",
                "alfredModel": "gpt-4.1-nano",
                "alfredInstructions": (
                    "## Objetivo\n"
                    "Oferecer suporte completo aos usuários do **Media Cuts Studio**, "
                    "garantindo a resolução rápida de problemas, registro organizado de tickets, "
                    "e coleta de feedback para melhoria contínua."
                ),
                "toolsEnabled": False,
            }
        }

        # Overlay de botConfig
        bc = default["botConfig"]
        bc["botToken"] = raw.get("botToken", bc["botToken"])
        bc["channelId"] = raw.get("channelId", bc["channelId"])
        bc["discordBotToken"] = raw.get("discordBotToken", bc["discordBotToken"])
        bc["discordChannelId"] = raw.get("discordChannelId", bc["discordChannelId"])
        bc["waServerUrl"] = raw.get("waServerUrl", bc["waServerUrl"])
        bc["waInstanceId"] = raw.get("waInstanceId", bc["waInstanceId"])
        bc["waApiKey"] = raw.get("waApiKey", bc["waApiKey"])
        bc["waSupportGroupJid"] = raw.get("waSupportGroupJid", bc["waSupportGroupJid"])

        # Overlay de moderationConfig
        mc = default["moderationConfig"]
        mc["autoModeration"] = raw.get("autoModeration", mc["autoModeration"])
        mc["aiModeration"]    = raw.get("aiModeration", mc["aiModeration"])
        mc["aiModerationModel"] = raw.get("aiModerationModel", mc["aiModerationModel"])
        mc["deleteSpam"]      = raw.get("deleteSpam", mc["deleteSpam"])
        mc["banThreshold"]    = raw.get("banThreshold", mc["banThreshold"])

        # Overlay de alfredConfig
        ac = default["alfredConfig"]
        ac["alfredName"]         = raw.get("alfredName", ac["alfredName"])
        ac["alfredModel"]        = raw.get("alfredModel", ac["alfredModel"])
        ac["alfredInstructions"] = raw.get("alfredInstructions", ac["alfredInstructions"])
        ac["toolsEnabled"]       = raw.get("toolsEnabled", ac["toolsEnabled"])

        result = {
            "botConfig": bc,
            "moderationConfig": mc,
            "alfredConfig": ac
        }
        logger.info("GET /api/config -> %s", result)
        return jsonify(result), 200

    except Exception as e:
        logger.exception("Erro em get_configurations")
        return jsonify({"error": "Erro interno ao buscar configurações"}), 500

def save_configurations():
    try:
        data = request.get_json() or {}
        db_ref.set(data)
        logger.info(f"Configurations saved: {data}")
        return jsonify({"message": "Configurações salvas com sucesso!"}), 200

    except Exception as e:
        logger.error(f"Error saving configurations: {e}")
        return jsonify({"error": "Erro ao salvar configurações."}), 500

# Roda o app quando executado diretamente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4959)















    