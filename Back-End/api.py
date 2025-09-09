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
    user_id = request.args.get("user_id") or (request.get_json() or {}).get("user_id")
    if not user_id:
        return jsonify({"error": "user_id obrigatório"}), 400

    if request.method == 'GET':
        try:
            configs = Config.query.filter_by(user_id=user_id).all()
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
                config = Config.query.filter_by(user_id=user_id, key=key).first()
                if config:
                    config.value = value
                else:
                    config = Config(user_id=user_id, key=key, value=value)
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

    # --- PEGAR USER_ID DO CONTEXTO ---
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id é obrigatório."}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404

    channel_id = request.form.get('channelId')
    caption = request.form.get('caption')

    try:
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        file_stats = os.stat(file_path)
        file_size_bytes = file_stats.st_size
        last_modified_timestamp = datetime.fromtimestamp(file_stats.st_mtime)

        # Salvar no PostgreSQL vinculado ao usuário
        alfred_file = AlfredFile(
            unique_filename=unique_filename,
            original_filename=file.filename,
            channel_id=channel_id,
            caption=caption,
            size_bytes=file_size_bytes,
            last_modified_local=last_modified_timestamp,
            local_path=file_path,
            url_download=f"/api/alfred-files/download/{unique_filename}",
            url_content=f"/api/alfred-files/{unique_filename}/content",
            uploaded_by_user_id=user.id   # <<< vinculação ao usuário
        )
        db_postgress.session.add(alfred_file)
        db_postgress.session.commit()

        return jsonify({
            "message": "Arquivo carregado com sucesso.",
            "fileId": unique_filename,
            "fileName": file.filename,
            "size": format_bytes(file_size_bytes),
            "lastModified": last_modified_timestamp.isoformat(),
            "uploadedBy": user.email
        }), 200

    except Exception as e:
        logger.exception(f"Erro no upload do arquivo: {e}")
        return jsonify({"error": "Erro no servidor ao processar o upload."}), 500


@app.route('/api/alfred-files', methods=['GET'])
def list_alfred_files():
    """
    Lista apenas os arquivos Alfred do usuário autenticado com seus metadados.
    """
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        alfred_files = AlfredFile.query.filter_by(uploaded_by_user_id=user_id).all()
        files_list = []

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
    Atualiza conteúdo de um arquivo Alfred apenas se pertence ao usuário.
    """
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        # Busca o arquivo do usuário
        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId, uploaded_by_user_id=user_id).first()
        if not alfred_file:
            return jsonify({"error": "Arquivo não encontrado para este usuário."}), 404

        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({"error": "'content' é obrigatório."}), 400

        new_content = data['content']
        if not isinstance(new_content, str):
            return jsonify({"error": "'content' deve ser string."}), 400

        if not os.path.exists(alfred_file.local_path):
            return jsonify({"error": "Arquivo não existe no disco."}), 404

        with open(alfred_file.local_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        file_stats = os.stat(alfred_file.local_path)
        last_modified_timestamp = datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc)

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
    Retorna conteúdo de um arquivo Alfred apenas se pertence ao usuário.
    """
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        # Busca o arquivo do usuário
        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId, uploaded_by_user_id=user_id).first()
        if not alfred_file:
            return jsonify({"error": "Arquivo não encontrado para este usuário."}), 404

        if not os.path.exists(alfred_file.local_path):
            return jsonify({"error": "Arquivo não existe no disco."}), 404

        file_extension = alfred_file.original_filename.rsplit('.', 1)[-1].lower() if '.' in alfred_file.original_filename else ''
        allowed_readable_extensions = {'md', 'txt', 'csv', 'json'}

        if file_extension not in allowed_readable_extensions:
            return jsonify({"error": "Visualização não suportada para este tipo de arquivo."}), 400

        with open(alfred_file.local_path, 'r', encoding='utf-8') as f:
            content = f.read()

        last_modified_timestamp = datetime.fromtimestamp(os.path.getmtime(alfred_file.local_path), tz=timezone.utc)

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
    Download de um arquivo Alfred, restrito ao usuário dono.
    """
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId, uploaded_by_user_id=user_id).first()
        if not alfred_file:
            return jsonify({"error": "Arquivo não encontrado para este usuário."}), 404

        if not os.path.exists(alfred_file.local_path):
            return jsonify({"error": "Arquivo não encontrado no disco."}), 404

        filename_on_disk = os.path.basename(alfred_file.local_path)

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
    Remove um arquivo Alfred apenas se pertence ao usuário do contexto.
    """
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        alfred_file = AlfredFile.query.filter_by(unique_filename=fileId, uploaded_by_user_id=user_id).first()
        if not alfred_file:
            return jsonify({"error": "Arquivo não encontrado para este usuário."}), 404

        if os.path.exists(alfred_file.local_path):
            os.remove(alfred_file.local_path)
            logger.info(f"Arquivo '{fileId}' excluído do disco.")

        db_postgress.session.delete(alfred_file)
        db_postgress.session.commit()

        return jsonify({"message": "Arquivo excluído com sucesso."}), 200

    except Exception as e:
        logger.exception(f"Erro ao excluir arquivo {fileId}: {e}")
        return jsonify({"error": "Erro interno ao excluir o arquivo."}), 500
    
@app.route('/api/messages/recent', methods=['GET'])
def list_recent_messages():
    """
    Lista interações recentes apenas do usuário autenticado.
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id é obrigatório."}), 400

    limit = request.args.get('limit', default=10, type=int)

    query = db.session.query(
        Message.session_id,
        func.max(Message.created_at).label('last_timestamp'),
        func.max(Message.id).label('last_message_id')
    ).filter_by(user_id=user_id).group_by(Message.session_id)

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
            "status": "responded"
        })

    return jsonify(interactions), 200

@app.route('/api/messages/<string:session_id>', methods=['GET'])
def get_interaction_details(session_id):
    """
    Retorna mensagens de uma interação, restrita ao usuário dono.
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id é obrigatório."}), 400

    messages = Message.query.filter_by(session_id=session_id, user_id=user_id).order_by(Message.created_at).all()
    if not messages:
        return jsonify({"error": "Interação não encontrada para este usuário."}), 404

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
        "status": "responded",
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
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        fifteen_minutes_ago = now - timedelta(minutes=15)

        # 1) messages in last hour for this user
        messages_in_last_hour = Message.query.filter(
            Message.user_id == user_id,
            Message.created_at >= one_hour_ago
        ).count()

        # 2) online users for this user context (if needed global, mantem tudo)
        online_users_count = User.query.filter(
            User.id == user_id,
            User.last_seen != None,
            User.last_seen >= fifteen_minutes_ago
        ).count()

        # 3) average response time (user -> assistant)
        total_response_time = 0.0
        response_count = 0

        msgs = Message.query.filter_by(user_id=user_id).order_by(Message.session_id, Message.created_at).all()
        from collections import defaultdict
        sessions = defaultdict(list)
        for m in msgs:
            sessions[m.session_id].append(m)

        for session_id, mlist in sessions.items():
            for i, m in enumerate(mlist):
                if m.role == 'user':
                    user_msg_time = m.created_at.replace(tzinfo=timezone.utc) if m.created_at.tzinfo is None else m.created_at
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
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', default=0, type=int)
        activity_type_filter = request.args.get('type')
        status_filter = request.args.get('status')
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        search_term = request.args.get('searchTerm', '').lower()

        if offset < 0:
            return jsonify({"error": "O parâmetro 'offset' deve ser um número inteiro não negativo."}), 400
        if limit is not None and limit <= 0:
            return jsonify({"error": "O parâmetro 'limit' deve ser um número inteiro positivo."}), 400

        valid_types = {'message', 'ban', 'unban', 'file', 'response', 'error', 'info', None}
        if activity_type_filter and activity_type_filter not in valid_types:
            return jsonify({"error": f"Tipo de atividade inválido."}), 400

        valid_statuses = {'success', 'warning', 'info', 'error', None}
        if status_filter and status_filter not in valid_statuses:
            return jsonify({"error": f"Status de atividade inválido."}), 400

        start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone.utc) if end_date_str else None

        all_activities = []
        activity_id_counter = 0

        # 1. Activities from messages (user only)
        msgs = Message.query.filter_by(user_id=user_id).order_by(Message.session_id, Message.created_at).all()
        from collections import defaultdict
        sessions = defaultdict(list)
        for m in msgs:
            sessions[m.session_id].append(m)

        for session_id, mlist in sessions.items():
            session_user_name = None
            for m in mlist:
                if m.user_id:
                    u = User.query.get(m.user_id)
                    if u:
                        session_user_name = u.name or u.email
                        break
            for idx, m in enumerate(mlist):
                activity_id_counter += 1
                timestamp = m.created_at.replace(tzinfo=timezone.utc) if m.created_at.tzinfo is None else m.created_at
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
                    continue
                all_activities.append(activity)

        # 2. Activities from files uploaded by this user
        files = AlfredFile.query.filter_by(uploaded_by_user_id=user_id).order_by(AlfredFile.uploaded_at.desc()).all()
        for f in files:
            activity_id_counter += 1
            ts = f.uploaded_at or datetime.now(timezone.utc)
            ts = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
            all_activities.append({
                "id": f"file_upload_{f.id}_{activity_id_counter}",
                "type": "file",
                "user": f.uploaded_by_user_id and (User.query.get(f.uploaded_by_user_id).name or User.query.get(f.uploaded_by_user_id).email) or "Sistema",
                "action": "Arquivo Carregado",
                "details": f"Arquivo '{f.original_filename}' ({f.unique_filename}) carregado.",
                "timestamp": ts.isoformat(),
                "status": "success"
            })

        # Filters
        filtered_activities = []
        for activity in all_activities:
            ts = datetime.fromisoformat(activity['timestamp']).replace(tzinfo=timezone.utc)
            if start_date and ts < start_date: continue
            if end_date and ts > end_date: continue
            if activity_type_filter and activity['type'] != activity_type_filter: continue
            if status_filter and activity.get('status') != status_filter: continue
            if search_term and search_term not in (activity.get('user') or '').lower() \
               and search_term not in (activity.get('action') or '').lower() \
               and search_term not in (activity.get('details') or '').lower():
                continue
            filtered_activities.append(activity)

        filtered_activities.sort(key=lambda x: datetime.fromisoformat(x['timestamp']), reverse=True)
        total_activities = len(filtered_activities)
        paginated = filtered_activities[offset:]
        if limit is not None: paginated = paginated[:limit]

        return jsonify({"total": total_activities, "activities": paginated}), 200

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
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        now = datetime.now(timezone.utc)
        today_24h_ago = now - timedelta(hours=24)
        yesterday_24h_ago = today_24h_ago - timedelta(hours=24)

        messages_today = Message.query.filter(
            Message.user_id == user_id,
            Message.created_at >= today_24h_ago
        ).all()
        messages_yesterday = Message.query.filter(
            Message.user_id == user_id,
            Message.created_at >= yesterday_24h_ago,
            Message.created_at < today_24h_ago
        ).all()

        active_users_today = {m.user_id for m in messages_today if m.user_id}
        active_users_yesterday = {m.user_id for m in messages_yesterday if m.user_id}

        alfred_responses_today = sum(1 for m in messages_today if m.role == "assistant")
        alfred_responses_yesterday = sum(1 for m in messages_yesterday if m.role == "assistant")

        files_managed = AlfredFile.query.filter_by(uploaded_by_user_id=user_id).count()

        def calculate_percentage_change(current, previous):
            if previous == 0:
                return current * 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 2)

        stats = {
            "totalMessages": len(messages_today) + len(messages_yesterday),
            "activeUsers": len(active_users_today),
            "alfredResponses": alfred_responses_today,
            "filesManaged": files_managed,
            "totalMessagesChangePercentage": calculate_percentage_change(len(messages_today), len(messages_yesterday)),
            "activeUsersChangePercentage": calculate_percentage_change(len(active_users_today), len(active_users_yesterday)),
            "alfredResponsesChangePercentage": calculate_percentage_change(alfred_responses_today, alfred_responses_yesterday)
        }

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao buscar as estatísticas do dashboard."}), 500


@app.route('/api/alfred/status', methods=['GET'])
def get_alfred_status():
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id é obrigatório."}), 400

        details = {
            "telegramApiConnected": False,
            "DiscordApiConnected": False,
            "WhatsAppApiConnected": False,
            "databaseConnected": True,
            "lastHeartbeat": None
        }

        current_status = "offline"
        current_message = "Alfred está offline ou inacessível."

        agents = AgentStatus.query.filter_by(user_id=user_id).all()
        now = datetime.now(timezone.utc)

        for agent in agents:
            heartbeat = agent.last_update.isoformat() if agent.last_update else None
            if agent.platform.lower() == "telegram":
                details["telegramApiConnected"] = (agent.status == "online")
                details["lastHeartbeat"] = heartbeat
                if agent.status == "online" and agent.last_update and (now - agent.last_update) < timedelta(days=1):
                    current_status = "online"
                    current_message = "(Telegram) Conectado."
                elif agent.status == "online":
                    current_status = "degraded"
                    current_message = "Alfred (Telegram) online, mas último update é antigo."
            elif agent.platform.lower() == "discord":
                details["DiscordApiConnected"] = (agent.status == "online")
            elif agent.platform.lower() == "whatsapp":
                details["WhatsAppApiConnected"] = (agent.status == "online")

        return jsonify({
            "status": current_status,
            "message": current_message,
            "details": details
        }), 200

    except Exception as e:
        logger.error(f"Internal server error when checking Alfred status: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Erro interno do servidor ao verificar o status do Alfred."
        }), 500

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















    