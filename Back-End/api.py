import os
import logging
import re
import json
import asyncio
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from agents import Agent, Runner
from pydantic import BaseModel
from typing import List, Dict
# from Alfred import Alfred # Uncomment if Alfred is used
from modules.Keys.Firebase.FirebaseApp import init_firebase
import firebase_admin
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


# Import da versão ultra melhorada
from ClienteChat.ai import CustomerChatAgent


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "modules", 'Keys', 'keys.env'))


try:
    # Cliente Docker global
    client = DockerClient(base_url='unix://var/run/docker.sock')
except docker.errors.DockerException as e:
    logger.warning(f"Não foi possível conectar ao Docker: {e}")
    client = None  # ou algum stub

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
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'alfred_knowledge')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Created upload directory: {UPLOAD_FOLDER}")
METADATA_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'alfred_files_metadata.json')
last_alfred_heartbeat = datetime.now(timezone.utc)
async def AgentAlfred():
    pass
    # Alfred_instance = Alfred(
    #     TelegramTOKEN,
    #     CHANNEL_ID
    # )

    # return resultados  # <-- retorna a lista com 3 dicts


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

@app.route('/api/Media_Cuts_Studio/AgentAlfred', methods=['POST'])
def api_AgentAlfred():
    pass

@app.route("/api/chat-assistant", methods=["POST"])
def chat_assistant():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "JSON payload required"}), 400

        user_msg = data.get("message", "").strip()
        if not user_msg:
            return jsonify({"success": False, "error": "Message field is required"}), 400
        logger.info(f"REQ  ")
        user_context = data.get("user_context", {})
        conversation_history = data.get("conversation_history", [])
        session_id = data.get("session_id") or str(uuid.uuid4())  # garante um id
        enable_analytics = data.get("enable_analytics", True)
        model = data.get("model", "gpt-5-nano")

        # Log input do usuário no Firebase
        save_message_to_firebase(session_id, "user", user_msg)

        enriched_context = _enrich_user_context(user_context, request)

        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "storage")
        result = asyncio.run(CustomerChatAgent(
            content_user=user_msg,
            UPLOAD_FOLDER=UPLOAD_FOLDER,
            user_context=enriched_context,
            conversation_history=conversation_history,
            model=model,
            UPLOAD_URL=UPLOAD_URL_VIDEOMANAGER,
            USER_ID=enriched_context.get("user_id", "anonymous"),
            enable_analytics=enable_analytics
        ))

        if result["success"]:
            response_data = _format_successful_response(result, session_id)
            agent_output = result["response"].content  # resposta do agente
            # Log output do assistente no Firebase
            save_message_to_firebase(session_id, "assistant", agent_output)
        else:
            response_data = _format_error_response(result, user_msg, session_id)
            save_message_to_firebase(session_id, "assistant", f"[ERRO] {result.get('error')}")

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
        return get_configurations()
    elif request.method == 'POST':
        return save_configurations()

@app.route('/api/alfred-files/upload', methods=['POST'])
def upload_alfred_file():
    """
    Handles file uploads for Alfred's knowledge base, saving files locally and metadata to Firebase.
    Receives a file, optional channelId, and caption.
    Stores the file in the 'alfred_knowledge' directory on the server.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo fornecido na requisição."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome do arquivo vazio."}), 400

    if not file:
        return jsonify({"error": "Arquivo inválido."}), 400

    channel_id = request.form.get('channelId')
    caption = request.form.get('caption')

    allowed_extensions = {'md', 'txt', 'pdf', 'docx', 'csv', 'json'}
    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

    if file_extension not in allowed_extensions:
        return jsonify({"error": f"Formato de arquivo não permitido. Apenas {', '.join(allowed_extensions)} são aceitos."}), 400

    try:
        unique_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        file.save(file_path)

        file_stats = os.stat(file_path)
        file_size_bytes = file_stats.st_size
        last_modified_timestamp = datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc) # Adicione tz=timezone.utc

        # --- ATUALIZAÇÃO PARA FIREBASE ---
        file_metadata = {
            "originalFileName": file.filename,
            "channelId": channel_id,
            "caption": caption,
            "size_bytes": file_size_bytes,
            "uploaded_at": datetime.now(timezone.utc).isoformat(), # Timestamp de upload
            "last_modified_local": last_modified_timestamp.isoformat(), # Última modificação no sistema de arquivos
            "local_path": file_path, # Armazena o caminho local no Firebase
            "url_download": f"/api/alfred-files/download/{unique_filename}", # URL para download
            "url_content": f"/api/alfred-files/{unique_filename}/content" # URL para obter conteúdo
        }
        # Salva os metadados no Firebase usando unique_filename como chave
        alfred_files_metadata_ref.child(unique_filename.replace('.', '_')).set(file_metadata)
        # --- FIM ATUALIZAÇÃO PARA FIREBASE ---

        response_data = {
            "message": "Arquivo carregado com sucesso.",
            "fileId": unique_filename.replace('.', '_'),
            "fileName": file.filename,
            "size": format_bytes(file_size_bytes),
            "lastModified": last_modified_timestamp.isoformat()
        }

        logger.info(f"File '{file.filename}' uploaded to '{file_path}' and metadata updated in Firebase.")

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error uploading file for Alfred: {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao processar o upload do arquivo."}), 500

@app.route('/api/alfred-files', methods=['GET'])
def list_alfred_files():
    """
    Handles GET requests to /api/alfred-files.
    Returns a list of all Alfred's configuration files with their metadata from Firebase.
    """
    try:
        files_list = []
        
        # --- ATUALIZAÇÃO PARA FIREBASE ---
        metadata = alfred_files_metadata_ref.get()
        if not metadata:
            logger.info("No Alfred file metadata found in Firebase.")
            return jsonify([]), 200
        # --- FIM ATUALIZAÇÃO PARA FIREBASE ---

        # metadata será um dicionário onde as chaves são os unique_filenames
        for unique_filename, file_info in metadata.items():
            if not isinstance(file_info, dict): # Proteção contra dados malformados no Firebase
                logger.warning(f"Skipping malformed metadata entry for '{unique_filename}': {file_info}")
                continue

            # Obter o caminho local do Firebase
            local_file_path = file_info.get("local_path")
            
            if not local_file_path or not os.path.exists(local_file_path):
                logger.warning(f"File '{unique_filename}' found in Firebase metadata but not on disk or path invalid: '{local_file_path}'. Skipping.")
                # Opcional: Remover entrada do Firebase se o arquivo local não existe
                # alfred_files_metadata_ref.child(unique_filename).delete()
                continue

            # Get actual file stats for the most up-to-date info
            file_stats = os.stat(local_file_path)
            last_modified_dt = datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc)

            files_list.append({
                "id": unique_filename,
                "name": file_info.get("originalFileName", unique_filename),
                "type": get_file_type(file_info.get("originalFileName", unique_filename)),
                "size": format_bytes(file_stats.st_size),
                "lastModified": last_modified_dt.isoformat(),
                "url": file_info.get("url_download"), # Usar a URL do Firebase
                "localPath": local_file_path # Adicionar o caminho local aqui
            })

        logger.info(f"Listed {len(files_list)} Alfred files from Firebase metadata.")
        return jsonify(files_list), 200

    except Exception as e:
        logger.error(f"Error listing Alfred files: {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao buscar a lista de arquivos."}), 500

@app.route('/api/alfred-files/<string:fileId>/content', methods=['PUT'])
def update_alfred_file_content(fileId):
    """
    Handles PUT requests to /api/alfred-files/{fileId}/content.
    Updates the content of a specific Alfred knowledge file locally and its metadata in Firebase.
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({"error": "Corpo da requisição inválido. 'content' é um campo obrigatório."}), 400

        new_content = data['content']
        if not isinstance(new_content, str):
            return jsonify({"error": "O campo 'content' deve ser uma string."}), 400

        # --- ATUALIZAÇÃO PARA FIREBASE ---
        # Tenta buscar os metadados primeiro para obter o local_path
        file_metadata_from_db = alfred_files_metadata_ref.child(fileId).get()
        if not file_metadata_from_db or not isinstance(file_metadata_from_db, dict):
            logger.warning(f"Metadata for file ID '{fileId}' not found or malformed in Firebase.")
            return jsonify({"error": "Metadados do arquivo não encontrados."}), 404
        
        file_path = file_metadata_from_db.get("local_path")
        if not file_path:
            logger.error(f"Local path not found in Firebase metadata for file ID '{fileId}'.")
            return jsonify({"error": "Caminho local do arquivo não configurado nos metadados."}), 500
        # --- FIM ATUALIZAÇÃO PARA FIREBASE ---

        if not os.path.exists(file_path):
            logger.warning(f"File with ID '{fileId}' not found at '{file_path}' (local disk).")
            # Opcional: Remover entrada do Firebase se o arquivo local não existe
            # alfred_files_metadata_ref.child(fileId).delete()
            return jsonify({"error": "Arquivo não encontrado no disco."}), 404

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        file_stats = os.stat(file_path)
        last_modified_timestamp = datetime.fromtimestamp(file_stats.st_mtime, tz=timezone.utc)
        
        # --- ATUALIZAÇÃO PARA FIREBASE ---
        # Atualiza os metadados no Firebase
        alfred_files_metadata_ref.child(fileId).update({
            "size_bytes": file_stats.st_size,
            "last_modified_local": last_modified_timestamp.isoformat(), # Atualiza o timestamp de modificação local
            "last_updated_firebase": datetime.now(timezone.utc).isoformat() # Timestamp da última atualização no Firebase
        })
        # --- FIM ATUALIZAÇÃO PARA FIREBASE ---

        logger.info(f"Content for file ID '{fileId}' updated successfully (local & Firebase).")
        return jsonify({
            "message": "Conteúdo do arquivo atualizado com sucesso.",
            "fileId": fileId,
            "lastModified": last_modified_timestamp.isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error updating content for file ID '{fileId}': {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao atualizar o conteúdo do arquivo."}), 500

@app.route('/api/alfred-files/<string:fileId>/content', methods=['GET'])
def get_alfred_file_content(fileId):
    """
    Handles GET requests to /api/alfred-files/{fileId}/content.
    Retrieves the textual content of a specific Alfred knowledge file, along with metadata from Firebase.
    """
    try:
        # 1. Buscar os metadados no Firebase usando o fileId modificado (com underscore)
        file_metadata_from_db = alfred_files_metadata_ref.child(fileId).get()
        if not file_metadata_from_db or not isinstance(file_metadata_from_db, dict):
            logger.warning(f"Metadata for file ID '{fileId}' not found or malformed in Firebase.")
            return jsonify({"error": "Metadados do arquivo não encontrados."}), 404
        
        # 2. Obter o caminho LOCAL REAL do arquivo do Firebase
        file_path = file_metadata_from_db.get("local_path")
        if not file_path:
            logger.error(f"Local path not found in Firebase metadata for file ID '{fileId}'.")
            return jsonify({"error": "Caminho local do arquivo não configurado nos metadados."}), 500
        
        # 3. Verificar se o arquivo existe no disco usando o local_path REAL
        if not os.path.exists(file_path):
            logger.warning(f"File with ID '{fileId}' (local path: '{file_path}') not found on disk.")
            # Opcional: Você pode remover a entrada do Firebase se o arquivo local não existe
            # alfred_files_metadata_ref.child(fileId).delete()
            return jsonify({"error": "Arquivo não encontrado no disco."}), 404

        # 4. Usar o originalFileName para determinar a extensão para validação
        original_file_name = file_metadata_from_db.get("originalFileName", "unknown")
        file_extension = original_file_name.rsplit('.', 1)[1].lower() if '.' in original_file_name else ''

        allowed_readable_extensions = {'md', 'txt', 'csv', 'json'} 
        
        if file_extension not in allowed_readable_extensions:
            logger.warning(f"Attempted to read content of non-text file '{fileId}' (original: {original_file_name}). Extension '{file_extension}' not supported for content viewing.")
            return jsonify({"error": "Visualização de conteúdo para este tipo de arquivo não é suportada."}), 400

        # 5. Ler o conteúdo do arquivo usando o local_path REAL
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        last_modified_timestamp = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)

        response_data = {
            "id": fileId, # Este é o ID do Firebase (com underscore)
            "name": original_file_name, # Nome original do arquivo (com ponto)
            "content": content,
            "lastModified": last_modified_timestamp.isoformat()
        }

        logger.info(f"Content for file ID '{fileId}' retrieved successfully.")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error retrieving content for file ID '{fileId}': {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao buscar o conteúdo do arquivo."}), 500

@app.route('/api/alfred-files/<string:fileId>/download', methods=['GET'])
def download_alfred_file(fileId):
    """
    Handles GET requests to /api/alfred-files/{fileId}/download.
    Allows downloading of a specific Alfred knowledge file, using its original filename and metadata from Firebase.
    """
    try:
        # 1. Buscar os metadados no Firebase usando o fileId modificado (com underscore)
        file_metadata_from_db = alfred_files_metadata_ref.child(fileId).get()
        if not file_metadata_from_db or not isinstance(file_metadata_from_db, dict):
            logger.warning(f"Metadata for file ID '{fileId}' not found or malformed in Firebase for download.")
            return jsonify({"error": "Metadados do arquivo não encontrados."}), 404
        
        # 2. Obter o originalFileName e o local_path REAL do arquivo do Firebase
        original_filename = file_metadata_from_db.get("originalFileName", fileId) # Fallback para fileId se não encontrar
        file_path = file_metadata_from_db.get("local_path")

        if not file_path:
            logger.error(f"Local path not found in Firebase metadata for file ID '{fileId}' during download.")
            return jsonify({"error": "Caminho local do arquivo não configurado nos metadados."}), 500
        
        # 3. Verificar se o arquivo existe no disco usando o local_path REAL
        if not os.path.exists(file_path):
            logger.warning(f"Download request for non-existent file ID: '{fileId}' (local path: '{file_path}').")
            # Opcional: Remover entrada do Firebase se o arquivo local não existe
            # alfred_files_metadata_ref.child(fileId).delete()
            return jsonify({"error": "Arquivo não encontrado no disco."}), 404

        logger.info(f"Serving download for file ID '{fileId}' (original name: '{original_filename}').")
        
        # send_from_directory precisa da pasta base e do NOME DO ARQUIVO DENTRO DESSA PASTA.
        # file_path é o caminho COMPLETO. Precisamos extrair apenas o nome do arquivo.
        # O nome do arquivo no disco é o último componente do file_path.
        filename_on_disk = os.path.basename(file_path)

        return send_from_directory(
            UPLOAD_FOLDER,           # O diretório base onde o arquivo está
            filename_on_disk,        # O nome real do arquivo no disco (com o ponto!)
            as_attachment=True,      # Força o download
            download_name=original_filename # Nome que o usuário verá ao baixar
        )
    except FileNotFoundError:
        logger.error(f"File not found during download process for ID '{fileId}'.", exc_info=True)
        return jsonify({"error": "Arquivo não encontrado."}), 404
    except Exception as e:
        logger.error(f"Error downloading file with ID '{fileId}': {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao tentar baixar o arquivo."}), 500
    
@app.route('/api/alfred-files/<string:fileId>', methods=['DELETE'])
def delete_alfred_file(fileId):
    """
    Handles DELETE requests to /api/alfred-files/{fileId}.
    Removes a specific Alfred knowledge file from local storage and its metadata from Firebase.
    """
    try:
        # --- ATUALIZAÇÃO PARA FIREBASE ---
        # Obter o local_path do Firebase antes de deletar
        file_metadata_from_db = alfred_files_metadata_ref.child(fileId).get()
        if not file_metadata_from_db or not isinstance(file_metadata_from_db, dict):
            logger.warning(f"Metadata for file ID '{fileId}' not found or malformed in Firebase for delete.")
            # Mesmo que não haja metadados, tentamos deletar o arquivo localmente para consistência
            file_path = os.path.join(UPLOAD_FOLDER, fileId) # Tentar um caminho padrão
        else:
            file_path = file_metadata_from_db.get("local_path")
            if not file_path:
                logger.error(f"Local path not found in Firebase metadata for file ID '{fileId}' during delete.")
                file_path = os.path.join(UPLOAD_FOLDER, fileId) # Fallback

        # 1. Delete the file from disk (if it exists)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File '{fileId}' successfully deleted from disk at '{file_path}'.")
        else:
            logger.warning(f"File '{fileId}' not found on disk at '{file_path}' during delete request.")

        # 2. Delete the metadata from Firebase
        alfred_files_metadata_ref.child(fileId).delete()
        logger.info(f"Metadata for file ID '{fileId}' successfully removed from Firebase.")
        # --- FIM ATUALIZAÇÃO PARA FIREBASE ---

        return jsonify({"message": "Arquivo excluído com sucesso."}), 200

    except Exception as e:
        logger.error(f"Error deleting file with ID '{fileId}': {e}", exc_info=True)
        return jsonify({"error": "Erro no servidor ao excluir o arquivo."}), 500

@app.route('/api/messages/recent', methods=['GET'])
def list_recent_messages():
    """
    Handles GET requests to /api/messages/recent.
    Retrieves a list of recent messages/interactions between users and Alfred,
    supporting filtering by limit, status, and after_id for pagination.
    """
    try:
        limit = request.args.get('limit', default=10, type=int)
        status_filter = request.args.get('status')
        after_id = request.args.get('after_id')

        if limit <= 0:
            return jsonify({"error": "O parâmetro 'limit' deve ser um número inteiro positivo."}), 400
        
        valid_statuses = {'pending', 'responded', 'resolved'}
        if status_filter and status_filter not in valid_statuses:
            return jsonify({"error": f"O parâmetro 'status' é inválido. Valores possíveis: {', '.join(valid_statuses)}."}), 400

        all_interactions_raw = messages_db_ref.get()

        if not all_interactions_raw:
            logger.info("No interactions found in Firebase.")
            return jsonify([]), 200

        interactions = []
        if isinstance(all_interactions_raw, dict):
            for interaction_id, interaction_data in all_interactions_raw.items():
                # --- START: ADIÇÃO PARA DEPURAÇÃO E TRATAMENTO DE ERRO DE DADOS MALFORMADOS ---
                if not isinstance(interaction_data, dict):
                    logger.error(f"Skipping malformed interaction: ID '{interaction_id}' contains data that is not a dictionary. Type: {type(interaction_data)}, Value: {interaction_data}")
                    continue # Pula para a próxima interação no loop
                # --- END: ADIÇÃO PARA DEPURAÇÃO E TRATAMENTO DE ERRO DE DADOS MALFORMADOS ---

                if 'user' in interaction_data and 'status' in interaction_data:
                    last_message_content = ""
                    last_message_timestamp = ""
                    
                    if 'messages' in interaction_data and isinstance(interaction_data['messages'], dict):
                        temp_messages_list = []
                        for msg_key, msg_value in interaction_data['messages'].items():
                            if isinstance(msg_value, dict) and 'timestamp' in msg_value:
                                msg_value['messageId'] = msg_key
                                temp_messages_list.append(msg_value)
                            else:
                                logger.warning(f"Skipping malformed message in interaction '{interaction_id}' message key '{msg_key}': {msg_value}")

                        if temp_messages_list:
                            temp_messages_list.sort(key=lambda x: datetime.fromisoformat(x['timestamp']), reverse=True)
                            last_message = temp_messages_list[0]
                            last_message_content = last_message.get('content', '')
                            last_message_timestamp = last_message.get('timestamp', '')
                        else:
                            last_message_timestamp = interaction_data.get('timestamp', '')
                            logger.warning(f"No valid messages found in interaction '{interaction_id}'. Using interaction timestamp if available: {last_message_timestamp}")
                    elif 'messages' in interaction_data and isinstance(interaction_data['messages'], list):
                        # Handle list case (less common for Firebase push keys, but possible)
                        temp_messages_list = []
                        for i, msg_value in enumerate(interaction_data['messages']):
                            if msg_value and isinstance(msg_value, dict) and 'timestamp' in msg_value:
                                msg_value['messageId'] = str(i)
                                temp_messages_list.append(msg_value)
                            else:
                                logger.warning(f"Skipping malformed list message in interaction '{interaction_id}' index '{i}': {msg_value}")
                        
                        if temp_messages_list:
                            temp_messages_list.sort(key=lambda x: datetime.fromisoformat(x['timestamp']), reverse=True)
                            last_message = temp_messages_list[0]
                            last_message_content = last_message.get('content', '')
                            last_message_timestamp = last_message.get('timestamp', '')
                        else:
                            last_message_timestamp = interaction_data.get('timestamp', '')
                            logger.warning(f"No valid messages found in interaction '{interaction_id}'. Using interaction timestamp if available: {last_message_timestamp}")
                    else:
                        last_message_timestamp = interaction_data.get('timestamp', '')
                        logger.warning(f"Interaction '{interaction_id}' has no 'messages' sub-node or it's not a dict/list. Using interaction timestamp: {last_message_timestamp}")


                    interactions.append({
                        "id": interaction_id,
                        "user": interaction_data.get('user', {}).get('name', 'Unknown User'),
                        "userId": interaction_data.get('user', {}).get('id', ''),
                        "message": last_message_content,
                        "timestamp": last_message_timestamp if last_message_timestamp else datetime.now(timezone.utc).isoformat(), # Fallback to now if no valid timestamp
                        "status": interaction_data.get('status', 'pending')
                    })
                else:
                    logger.warning(f"Skipping malformed interaction entry with ID '{interaction_id}': Missing 'user' or 'status' fields. Data: {interaction_data}")


        # Sort interactions by their (last) message timestamp in descending order (most recent first)
        try:
            sortable_interactions = []
            non_sortable_interactions = []
            for i in interactions:
                if i['timestamp']:
                    try:
                        # Ensure timestamp has timezone info before sorting
                        dt_obj = datetime.fromisoformat(i['timestamp'])
                        if dt_obj.tzinfo is None:
                            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                        i['parsed_timestamp'] = dt_obj # Store parsed for sorting
                        sortable_interactions.append(i)
                    except ValueError:
                        logger.warning(f"Invalid timestamp format in interaction ID {i.get('id', 'N/A')}: {i['timestamp']}. Cannot sort.")
                        non_sortable_interactions.append(i)
                else:
                    non_sortable_interactions.append(i)

            sortable_interactions.sort(key=lambda x: x['parsed_timestamp'], reverse=True)
            
            # Remove the temporary 'parsed_timestamp' field before returning
            for i in sortable_interactions:
                i.pop('parsed_timestamp', None)
            
            messages_to_return = sortable_interactions + non_sortable_interactions
        except Exception as e: # Captura erros gerais de ordenação, incluindo ValueErrors de fromisoformat
            logger.error(f"Error during sorting of interactions: {e}. Check Firebase data structure and timestamp formats.")
            return jsonify({"error": "Erro interno ao processar dados de interação: formato de 'timestamp' incorreto ou problema na ordenação."}), 500

        filtered_messages_summary = []
        start_collecting = not after_id

        for interaction_summary in messages_to_return:
            if after_id and interaction_summary['id'] == after_id:
                start_collecting = True
                continue

            if not start_collecting:
                continue

            if status_filter and interaction_summary.get('status') != status_filter:
                continue

            filtered_messages_summary.append(interaction_summary)

            if len(filtered_messages_summary) >= limit:
                break

        logger.info(f"Retrieved {len(filtered_messages_summary)} recent interaction summaries with limit={limit}, status={status_filter}, after_id={after_id}.")
        return jsonify(filtered_messages_summary), 200

    except ValueError as ve:
        logger.error(f"Bad Request (validation error): {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Critical error listing recent messages: {e}", exc_info=True) # exc_info=True para stack trace
        return jsonify({"error": "Erro crítico no servidor ao buscar as mensagens recentes. Verifique os logs do servidor."}), 500

@app.route('/api/messages/<string:interactionId>', methods=['GET'])
def get_interaction_details(interactionId):
    """
    Handles GET requests to /api/messages/{interactionId}.
    Retrieves the complete message history for a specific interaction/ticket.
    """
    try:
        # Fetch the specific interaction data from Firebase
        interaction_data = messages_db_ref.child(interactionId).get()

        if not interaction_data:
            logger.warning(f"Interaction with ID '{interactionId}' not found in Firebase.")
            return jsonify({"error": "Interação/Ticket não encontrado."}), 404

        # Extract user information
        user_info = interaction_data.get('user', {})
        
        # Extract status
        status = interaction_data.get('status', 'unknown')

        # Extract and format messages within the interaction
        raw_messages = interaction_data.get('messages', {})
        formatted_messages = []

        if isinstance(raw_messages, dict):
            for msg_id, msg_content in raw_messages.items():
                if isinstance(msg_content, dict) and 'sender' in msg_content and 'timestamp' in msg_content and 'content' in msg_content:
                    formatted_messages.append({
                        "messageId": msg_id,
                        "sender": msg_content['sender'],
                        "timestamp": msg_content['timestamp'],
                        "content": msg_content['content']
                    })
                else:
                    logger.warning(f"Malformed message object in interaction '{interactionId}', skipping message ID '{msg_id}': {msg_content}")
        elif isinstance(raw_messages, list):
            # If Firebase somehow returned a list (e.g., if you used integer keys for messages)
            for i, msg_content in enumerate(raw_messages):
                 if msg_content and isinstance(msg_content, dict) and 'sender' in msg_content and 'timestamp' in msg_content and 'content' in msg_content:
                    formatted_messages.append({
                        "messageId": str(i), # Use index as messageId or generate unique
                        "sender": msg_content['sender'],
                        "timestamp": msg_content['timestamp'],
                        "content": msg_content['content']
                    })
                 else:
                    logger.warning(f"Malformed message object in interaction '{interactionId}' at index {i}, skipping: {msg_content}")
        
        # Sort messages by timestamp within the interaction
        if formatted_messages:
            try:
                formatted_messages.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))
            except (KeyError, ValueError) as e:
                logger.error(f"Error sorting messages for interaction '{interactionId}': {e}")
                # Decide how to handle: send unsorted, filter out bad ones, or return error
                # For now, we'll log and continue with potentially unsorted if there's a problem
                pass 


        response_data = {
            "interactionId": interactionId,
            "user": {
                "name": user_info.get('name', 'Unknown'),
                "id": user_info.get('id', ''),
                "platform": user_info.get('platform', 'N/A')
            },
            "status": status,
            "messages": formatted_messages
        }

        logger.info(f"Retrieved details for interaction ID '{interactionId}'.")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error retrieving details for interaction ID '{interactionId}': {e}")
        return jsonify({"error": "Erro no servidor ao buscar os detalhes da conversa."}), 500

@app.route('/api/users', methods=['GET'])
def list_users():
    """
    Handles GET requests to /api/users.
    Returns a list of users who interacted with the bot, with filtering and pagination.
    """
    try:
        search_term = request.args.get('searchTerm', '').lower()
        status_filter = request.args.get('status', '').lower()
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', default=0, type=int)

        if offset < 0:
            return jsonify({"error": "O parâmetro 'offset' deve ser um número inteiro não negativo."}), 400
        if limit is not None and limit <= 0:
            return jsonify({"error": "O parâmetro 'limit' deve ser um número inteiro positivo."}), 400

        valid_statuses = {'active', 'banned', ''} # Empty string allows all statuses if no filter
        if status_filter and status_filter not in valid_statuses:
            return jsonify({"error": f"O parâmetro 'status' é inválido. Valores possíveis: {', '.join(s for s in valid_statuses if s)}."}), 400

        all_users_raw = users_db_ref.get()

        if not all_users_raw:
            return jsonify([]), 200 # No users found

        users_list = []
        if isinstance(all_users_raw, dict):
            for user_platform_id, user_data in all_users_raw.items():
                if isinstance(user_data, dict) and 'name' in user_data and 'username' in user_data and 'userId' in user_data and 'status' in user_data:
                    # 'id' is internal, 'userId' is platform ID. We'll use platform ID for consistency
                    # or you can generate an internal ID if your system needs it.
                    # For simplicity, using the Firebase key (user_platform_id) as the 'id' here.
                    users_list.append({
                        "id": user_platform_id, # Or user_data.get('id', user_platform_id) if stored
                        "name": user_data.get('name', 'N/A'),
                        "username": user_data.get('username', 'N/A'),
                        "userId": user_data.get('userId', user_platform_id), # Telegram User ID
                        "status": user_data.get('status', 'active'),
                        "lastSeen": user_data.get('lastSeen', datetime.now().isoformat()),
                        "messageCount": user_data.get('messageCount', 0)
                    })
                else:
                    logger.warning(f"Skipping malformed user entry with ID '{user_platform_id}': {user_data}")
        elif isinstance(all_users_raw, list):
            # Less common for Firebase user lists, but handled
            for i, user_data in enumerate(all_users_raw):
                if user_data and isinstance(user_data, dict) and 'name' in user_data: # Basic check
                    users_list.append({
                        "id": str(i),
                        "name": user_data.get('name', 'N/A'),
                        "username": user_data.get('username', 'N/A'),
                        "userId": user_data.get('userId', str(i)),
                        "status": user_data.get('status', 'active'),
                        "lastSeen": user_data.get('lastSeen', datetime.now().isoformat()),
                        "messageCount": user_data.get('messageCount', 0)
                    })
                else:
                    logger.warning(f"Skipping malformed user entry at index {i}: {user_data}")


        # Apply filters
        filtered_users = []
        for user in users_list:
            match_search = True
            if search_term:
                user_name = user.get('name', '').lower()
                user_username = user.get('username', '').lower()
                user_id = user.get('userId', '').lower()
                if not (search_term in user_name or search_term in user_username or search_term in user_id):
                    match_search = False
            
            match_status = True
            if status_filter and user.get('status') != status_filter:
                match_status = False

            if match_search and match_status:
                filtered_users.append(user)
        
        # Sort users (e.g., by name or lastSeen for consistency)
        # For simplicity, let's sort by name for now. You can adjust this.
        filtered_users.sort(key=lambda x: x.get('name', '').lower())

        # Apply pagination
        paginated_users = filtered_users[offset:]
        if limit is not None:
            paginated_users = paginated_users[:limit]

        logger.info(f"Retrieved {len(paginated_users)} users with searchTerm='{search_term}', status='{status_filter}', limit={limit}, offset={offset}.")
        return jsonify(paginated_users), 200

    except ValueError as ve:
        logger.error(f"Bad Request: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({"error": "Erro no servidor ao buscar a lista de usuários."}), 500

@app.route('/api/users/<string:userId>/ban', methods=['POST'])
def ban_user(userId):
    """
    Handles POST requests to /api/users/{userId}/ban.
    Marks a user as banned in Firebase and includes a placeholder for platform-specific banning.
    """
    try:
        user_ref = users_db_ref.child(userId)
        user_data = user_ref.get()

        if not user_data:
            logger.warning(f"Ban request for non-existent user ID: '{userId}'.")
            return jsonify({"error": "Usuário não encontrado."}), 404

        if user_data.get('status') == 'banned':
            logger.info(f"User ID '{userId}' is already banned.")
            return jsonify({
                "message": "Usuário já está banido.",
                "userId": userId,
                "status": "banned"
            }), 200 # Or 400 if you prefer to enforce no-op for already banned users

        # Update user status in Firebase
        update_data = {"status": "banned"}
        
        request_body = request.get_json(silent=True)
        reason = None
        duration = None

        if request_body:
            reason = request_body.get('reason')
            duration = request_body.get('duration')
            if reason:
                update_data["banReason"] = reason
            if duration:
                update_data["banDuration"] = duration
        
        user_ref.update(update_data)
        logger.info(f"User ID '{userId}' status updated to 'banned' in Firebase. Reason: '{reason}', Duration: '{duration}'.")

        # --- Placeholder for platform-specific banning logic ---
        # This is where you would integrate with your bot's platform API (e.g., Telegram Bot API)
        # to actually ban the user from a channel or group.
        #
        # Example (conceptual):
        # try:
        #     if user_data.get('platform') == 'Telegram':
        #         # Call Telegram Bot API to ban user
        #         # telegram_api.ban_chat_member(chat_id=YOUR_CHANNEL_ID, user_id=userId)
        #         logger.info(f"Attempted to ban Telegram user '{userId}' on platform.")
        #     elif user_data.get('platform') == 'Discord':
        #         # Call Discord API to ban user
        #         # discord_api.ban_guild_member(guild_id=YOUR_GUILD_ID, user_id=userId)
        #         logger.info(f"Attempted to ban Discord user '{userId}' on platform.")
        #     else:
        #         logger.warning(f"No platform-specific ban logic for user '{userId}' on platform '{user_data.get('platform')}'")
        # except Exception as platform_e:
        #     logger.error(f"Failed to ban user '{userId}' on platform API: {platform_e}")
        #     # You might want to revert Firebase status or flag this as a partial failure
        #     # return jsonify({"error": "Usuário banido no sistema, mas falha ao banir na plataforma."}), 500
        # ----------------------------------------------------

        return jsonify({
            "message": "Usuário banido com sucesso.",
            "userId": userId,
            "status": "banned"
        }), 200

    except Exception as e:
        logger.error(f"Error banning user '{userId}': {e}")
        return jsonify({"error": "Erro no servidor ao banir o usuário."}), 500

@app.route('/api/users/<string:userId>/unban', methods=['POST'])
def unban_user(userId):
    """
    Handles POST requests to /api/users/{userId}/unban.
    Removes the banned status from a user in Firebase and includes a placeholder for platform-specific unbanning.
    """
    try:
        user_ref = users_db_ref.child(userId)
        user_data = user_ref.get()

        if not user_data:
            logger.warning(f"Unban request for non-existent user ID: '{userId}'.")
            return jsonify({"error": "Usuário não encontrado."}), 404

        if user_data.get('status') == 'active':
            logger.info(f"User ID '{userId}' is already active (not banned).")
            return jsonify({
                "message": "Usuário já está ativo (não banido).",
                "userId": userId,
                "status": "active"
            }), 200 # Or 400 if you prefer to enforce no-op for already active users

        # Update user status in Firebase to 'active'
        update_data = {"status": "active"}
        
        # Optionally remove ban reason and duration if they exist
        if "banReason" in user_data:
            update_data["banReason"] = None # Set to None to remove the field
        if "banDuration" in user_data:
            update_data["banDuration"] = None # Set to None to remove the field
        
        user_ref.update(update_data)
        logger.info(f"User ID '{userId}' status updated to 'active' in Firebase.")

        # --- Placeholder for platform-specific unbanning logic ---
        # This is where you would integrate with your bot's platform API (e.g., Telegram Bot API)
        # to actually unban the user from a channel or group.
        #
        # Example (conceptual):
        # try:
        #     if user_data.get('platform') == 'Telegram':
        #         # Call Telegram Bot API to unban user (e.g., unbanChatMember or similar)
        #         # telegram_api.unban_chat_member(chat_id=YOUR_CHANNEL_ID, user_id=userId)
        #         logger.info(f"Attempted to unban Telegram user '{userId}' on platform.")
        #     elif user_data.get('platform') == 'Discord':
        #         # Call Discord API to unban user (e.g., unban_guild_member)
        #         # discord_api.unban_guild_member(guild_id=YOUR_GUILD_ID, user_id=userId)
        #         logger.info(f"Attempted to unban Discord user '{userId}' on platform.")
        #     else:
        #         logger.warning(f"No platform-specific unban logic for user '{userId}' on platform '{user_data.get('platform')}'")
        # except Exception as platform_e:
        #     logger.error(f"Failed to unban user '{userId}' on platform API: {platform_e}")
        #     # You might want to revert Firebase status or flag this as a partial failure
        #     # return jsonify({"error": "Usuário desbanido no sistema, mas falha ao desbanir na plataforma."}), 500
        # ----------------------------------------------------

        return jsonify({
            "message": "Usuário desbanido com sucesso.",
            "userId": userId,
            "status": "active"
        }), 200

    except Exception as e:
        logger.error(f"Error unbanning user '{userId}': {e}")
        return jsonify({"error": "Erro no servidor ao desbanir o usuário."}), 500

@app.route('/api/metrics/realtime', methods=['GET'])
def get_realtime_metrics():
    """
    Handles GET requests to /api/metrics/realtime.
    Provides aggregated real-time data about bot activity.
    """
    try:
        now = datetime.now(timezone.utc) # Use timezone-aware datetime for comparison
        one_hour_ago = now - timedelta(hours=1)
        fifteen_minutes_ago = now - timedelta(minutes=15)

        all_interactions_raw = messages_db_ref.get()
        all_users_raw = users_db_ref.get()

        messages_in_last_hour = 0
        online_users_ids = set()
        total_response_time = 0.0
        response_count = 0

        if isinstance(all_interactions_raw, dict):
            for interaction_id, interaction_data in all_interactions_raw.items():
                if isinstance(interaction_data, dict) and 'messages' in interaction_data:
                    user_id = interaction_data.get('user', {}).get('id')
                    
                    if isinstance(interaction_data['messages'], (dict, list)):
                        messages_in_interaction = []
                        if isinstance(interaction_data['messages'], dict):
                            messages_in_interaction = list(interaction_data['messages'].values())
                        elif isinstance(interaction_data['messages'], list):
                            messages_in_interaction = [msg for msg in interaction_data['messages'] if msg is not None]

                        for msg in messages_in_interaction:
                            if isinstance(msg, dict) and 'timestamp' in msg and 'sender' in msg and 'content' in msg:
                                try:
                                    msg_timestamp = datetime.fromisoformat(msg['timestamp'])
                                    # Ensure timestamp is timezone-aware, assume UTC if not specified
                                    if msg_timestamp.tzinfo is None:
                                        msg_timestamp = msg_timestamp.replace(tzinfo=timezone.utc)

                                    if msg_timestamp >= one_hour_ago:
                                        messages_in_last_hour += 1
                                    
                                    if msg_timestamp >= fifteen_minutes_ago and user_id:
                                        online_users_ids.add(user_id)

                                    # Calculate response time
                                    if msg['sender'] == 'user':
                                        user_msg_time = msg_timestamp
                                        # Look for the immediate next message from 'Alfred' in the same interaction
                                        for subsequent_msg in messages_in_interaction:
                                            if isinstance(subsequent_msg, dict) and 'timestamp' in subsequent_msg and 'sender' in subsequent_msg and subsequent_msg['sender'] == 'Alfred':
                                                alfred_msg_time = datetime.fromisoformat(subsequent_msg['timestamp'])
                                                if alfred_msg_time.tzinfo is None:
                                                    alfred_msg_time = alfred_msg_time.replace(tzinfo=timezone.utc)
                                                
                                                if alfred_msg_time > user_msg_time:
                                                    time_diff = (alfred_msg_time - user_msg_time).total_seconds()
                                                    if time_diff >= 0: # Ensure positive response time
                                                        total_response_time += time_diff
                                                        response_count += 1
                                                        break # Found response for this user message, move to next user message
                                except ValueError as ve:
                                    logger.warning(f"Invalid timestamp format in message: {msg.get('timestamp', 'N/A')} - {ve}")
                            else:
                                logger.warning(f"Skipping malformed message entry in interaction '{interaction_id}': {msg}")
                else:
                    logger.warning(f"Skipping malformed messages structure in interaction '{interaction_id}': {interaction_data.get('messages')}")


        online_users_count = len(online_users_ids)
        average_response_time = total_response_time / response_count if response_count > 0 else 0.0

        metrics = {
            "messagesPerHour": messages_in_last_hour,
            "onlineUsers": online_users_count,
            "averageResponseTime": round(average_response_time, 2)
        }

        logger.info(f"Real-time metrics calculated: {metrics}")
        return jsonify(metrics), 200

    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        return jsonify({"error": "Erro no servidor ao calcular ou buscar as métricas."}), 500

@app.route('/api/activities', methods=['GET'])
def list_activities():
    """
    Handles GET requests to /api/activities.
    Returns a paginated and filterable list of all recorded bot activities.
    """
    try:
        # Parse query parameters
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', default=0, type=int)
        activity_type_filter = request.args.get('type')
        status_filter = request.args.get('status')
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        search_term = request.args.get('searchTerm', '').lower()

        # Input validation
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
        activity_id_counter = 0 # Simple counter for unique activity IDs

        # --- 1. Gather activities from Firebase Messages ---
        all_interactions_raw = messages_db_ref.get()
        if isinstance(all_interactions_raw, dict):
            for interaction_id, interaction_data in all_interactions_raw.items():
                if isinstance(interaction_data, dict) and 'messages' in interaction_data:
                    user_name = interaction_data.get('user', {}).get('name', 'Unknown User')
                    user_id = interaction_data.get('user', {}).get('id', 'N/A')
                    
                    if isinstance(interaction_data['messages'], (dict, list)):
                        messages_in_interaction = []
                        if isinstance(interaction_data['messages'], dict):
                            messages_in_interaction = list(interaction_data['messages'].values())
                        elif isinstance(interaction_data['messages'], list):
                            messages_in_interaction = [msg for msg in interaction_data['messages'] if msg is not None]

                        for msg_idx, msg in enumerate(messages_in_interaction):
                            if isinstance(msg, dict) and 'timestamp' in msg and 'sender' in msg and 'content' in msg:
                                try:
                                    msg_timestamp = datetime.fromisoformat(msg['timestamp'])
                                    if msg_timestamp.tzinfo is None:
                                        msg_timestamp = msg_timestamp.replace(tzinfo=timezone.utc)

                                    activity_id_counter += 1
                                    activity_id = f"msg_{interaction_id}_{msg_idx}"
                                    
                                    activity = {
                                        "id": activity_id,
                                        "timestamp": msg_timestamp.isoformat(),
                                        "status": "success", # Assuming message processing is usually successful
                                    }

                                    if msg['sender'] == 'user':
                                        activity["type"] = "message"
                                        activity["user"] = user_name
                                        activity["action"] = "Enviou mensagem"
                                        activity["details"] = f"Usuário '{user_name}' ({user_id}) enviou: {msg['content'][:100]}..." if len(msg['content']) > 100 else f"Usuário '{user_name}' ({user_id}) enviou: {msg['content']}"
                                    elif msg['sender'] == 'Alfred':
                                        activity["type"] = "response"
                                        activity["user"] = "Alfred (Bot)"
                                        activity["action"] = "Respondeu à mensagem"
                                        activity["details"] = f"Alfred respondeu a '{user_name}' ({user_id}): {msg['content'][:100]}..." if len(msg['content']) > 100 else f"Alfred respondeu a '{user_name}' ({user_id}): {msg['content']}"
                                    else:
                                        # Skip unknown senders
                                        continue
                                    
                                    all_activities.append(activity)
                                except ValueError as ve:
                                    logger.warning(f"Skipping activity from malformed timestamp in message: {msg.get('timestamp', 'N/A')} - {ve}")
                            else:
                                logger.warning(f"Skipping malformed message object within interaction '{interaction_id}': {msg}")
                    else:
                        logger.warning(f"Skipping malformed messages structure in interaction '{interaction_id}': {interaction_data['messages']}")
                else:
                    logger.warning(f"Skipping malformed interaction entry: {interaction_id}")

        # --- 2. Gather activities from Firebase Users (for ban/unban status changes) ---
        # Note: This gives current status. A true log would require historical data.
        all_users_raw = users_db_ref.get()
        if isinstance(all_users_raw, dict):
            for user_platform_id, user_data in all_users_raw.items():
                if isinstance(user_data, dict):
                    activity_id_counter += 1
                    user_name = user_data.get('name', 'N/A')
                    user_status = user_data.get('status', 'active')
                    last_seen_str = user_data.get('lastSeen') # Using lastSeen as a proxy for timestamp

                    if user_status == 'banned':
                        ban_reason = user_data.get('banReason', 'Motivo não especificado')
                        ban_duration = user_data.get('banDuration', 'Não especificada')
                        timestamp = last_seen_str if last_seen_str else datetime.now(timezone.utc).isoformat()
                        
                        all_activities.append({
                            "id": f"ban_{user_platform_id}_{activity_id_counter}",
                            "type": "ban",
                            "user": user_name,
                            "action": "Usuário Banido",
                            "details": f"Usuário '{user_name}' ({user_platform_id}) foi banido. Motivo: '{ban_reason}'. Duração: '{ban_duration}'.",
                            "timestamp": timestamp,
                            "status": "warning" # Or success, depending on your perspective
                        })
                    # We can't reliably infer 'unban' events without historical data.
                    # This would need to be logged when the unban API call happens.

        # --- 3. Gather activities from Alfred Files Metadata (uploads/deletions) ---
        if os.path.exists(METADATA_FILE_PATH):
            with open(METADATA_FILE_PATH, 'r') as f:
                try:
                    file_metadata = json.load(f)
                    for file_id, file_info in file_metadata.items():
                        activity_id_counter += 1
                        uploaded_at_str = file_info.get("uploaded_at")
                        original_file_name = file_info.get("originalFileName", file_id)
                        
                        if uploaded_at_str:
                            try:
                                timestamp = datetime.fromisoformat(uploaded_at_str)
                                if timestamp.tzinfo is None:
                                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                                all_activities.append({
                                    "id": f"file_upload_{file_id}_{activity_id_counter}",
                                    "type": "file",
                                    "user": "Sistema (Admin)", # Assuming uploads are by admins
                                    "action": "Arquivo Carregado",
                                    "details": f"Arquivo '{original_file_name}' ({file_id}) carregado para a base de conhecimento de Alfred.",
                                    "timestamp": timestamp.isoformat(),
                                    "status": "success"
                                })
                            except ValueError as ve:
                                logger.warning(f"Skipping activity from malformed timestamp in file metadata: {uploaded_at_str} - {ve}")
                except json.JSONDecodeError:
                    logger.warning(f"Metadata file '{METADATA_FILE_PATH}' is empty or corrupted. Skipping file activities.")
        
        # Note: Deletions would require comparing current metadata with previous state or explicit logging.
        # For a truly accurate log, deletions should trigger a log entry at the time of deletion.


        # --- 4. Apply Filters ---
        filtered_activities = []
        for activity in all_activities:
            activity_timestamp = datetime.fromisoformat(activity['timestamp'])
            
            # Ensure activity_timestamp is timezone-aware for comparison
            if activity_timestamp.tzinfo is None:
                activity_timestamp = activity_timestamp.replace(tzinfo=timezone.utc)

            # Date range filter
            if start_date and activity_timestamp < start_date:
                continue
            if end_date and activity_timestamp > end_date:
                continue

            # Type filter
            if activity_type_filter and activity['type'] != activity_type_filter:
                continue

            # Status filter
            if status_filter and activity['status'] != status_filter:
                continue

            # Search term filter
            if search_term:
                user_match = search_term in activity.get('user', '').lower()
                action_match = search_term in activity.get('action', '').lower()
                details_match = search_term in activity.get('details', '').lower()
                if not (user_match or action_match or details_match):
                    continue
            
            filtered_activities.append(activity)

        # --- 5. Sort Activities (most recent first) ---
        try:
            filtered_activities.sort(key=lambda x: datetime.fromisoformat(x['timestamp']), reverse=True)
        except ValueError as e:
            logger.error(f"Error sorting activities by timestamp: {e}")
            # If sorting fails due to bad timestamps, we can still return unsorted,
            # but it's better to ensure data quality.

        # --- 6. Apply Pagination ---
        total_activities = len(filtered_activities)
        paginated_activities = filtered_activities[offset:]
        if limit is not None:
            paginated_activities = paginated_activities[:limit]

        logger.info(f"Retrieved {len(paginated_activities)} activities (total filtered: {total_activities}) with filters: {request.args}.")

        return jsonify({
            "total": total_activities,
            "activities": paginated_activities
        }), 200

    except ValueError as ve:
        logger.error(f"Bad Request for activities: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error listing activities: {e}")
        return jsonify({"error": "Erro no servidor ao buscar o log de atividades."}), 500

@app.route('/api/activities', methods=['DELETE'])
def clear_activities():
    """
    Handles DELETE requests to /api/activities.
    Deletes a subset of activities from the log based on filters.
    Currently, this only affects the 'messages' collection in Firebase.
    """
    try:
        # Check for authorization here if you have an admin user system
        # For example: if not is_admin_user(request.headers.get('Authorization')):
        #     return jsonify({"error": "Usuário não autorizado a limpar o log."}), 403

        before_date_str = request.args.get('beforeDate')
        status_filter = request.args.get('status') # This filter is tricky for deleting messages

        deleted_count = 0

        # Validate beforeDate
        before_date = None
        if before_date_str:
            try:
                before_date = datetime.fromisoformat(before_date_str)
                if before_date.tzinfo is None:
                    before_date = before_date.replace(tzinfo=timezone.utc)
            except ValueError:
                return jsonify({"error": "Formato de 'beforeDate' inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)."}), 400

        # Validate status filter (only relevant if you're deleting specific types of activities with explicit statuses)
        # For messages, the status is usually 'success' or 'pending/responded' based on interaction status.
        # This delete operation mainly focuses on message age, not their interaction status.
        # So, if a status filter is provided, it might not yield expected results for message deletion directly.
        valid_statuses = {'success', 'warning', 'info', 'error', None} # Adding None for no filter
        if status_filter and status_filter not in valid_statuses:
            return jsonify({"error": f"O status de atividade '{status_filter}' é inválido para exclusão. Valores possíveis: {', '.join(s for s in valid_statuses if s)}."}), 400


        # --- Deleting from Firebase Messages Collection ---
        # Get all interactions to filter locally
        all_interactions_raw = messages_db_ref.get()
        interactions_to_delete = []

        if isinstance(all_interactions_raw, dict):
            for interaction_id, interaction_data in all_interactions_raw.items():
                if isinstance(interaction_data, dict) and 'messages' in interaction_data:
                    # Collect message timestamps to determine if interaction should be deleted
                    earliest_message_timestamp = None
                    
                    if isinstance(interaction_data['messages'], (dict, list)):
                        messages_in_interaction = []
                        if isinstance(interaction_data['messages'], dict):
                            messages_in_interaction = list(interaction_data['messages'].values())
                        elif isinstance(interaction_data['messages'], list):
                            messages_in_interaction = [msg for msg in interaction_data['messages'] if msg is not None]

                        if messages_in_interaction:
                            # Find the earliest message timestamp in the interaction
                            try:
                                # Sort by timestamp to find the earliest
                                messages_in_interaction.sort(key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01T00:00:00Z')))
                                earliest_message_timestamp = datetime.fromisoformat(messages_in_interaction[0].get('timestamp'))
                                if earliest_message_timestamp.tzinfo is None:
                                    earliest_message_timestamp = earliest_message_timestamp.replace(tzinfo=timezone.utc)
                            except (KeyError, ValueError) as e:
                                logger.warning(f"Could not determine earliest timestamp for interaction {interaction_id}: {e}. Skipping deletion for this interaction based on date.")
                                earliest_message_timestamp = None # Cannot filter by date, so skip this interaction for date-based deletion


                    # If a beforeDate is provided and the earliest message in this interaction is older,
                    # mark the entire interaction for deletion.
                    # Note: We are deleting entire interactions, not individual messages within an interaction,
                    # because Firebase Realtime Database is tree-based. Deleting individual messages would be more complex
                    # and potentially leave empty interaction nodes.
                    if before_date and earliest_message_timestamp and earliest_message_timestamp < before_date:
                        interactions_to_delete.append(interaction_id)
                    # For status_filter, it's hard to apply to entire interactions here
                    # as 'success' is the default for messages, and interaction status is 'pending/responded'.
                    # This would require more sophisticated logic if you want to delete based on `interaction.status`.
                    # For simplicity, we're primarily using `beforeDate` for message log clearing.


        # Perform deletion
        for interaction_id in interactions_to_delete:
            messages_db_ref.child(interaction_id).delete()
            deleted_count += 1
            logger.info(f"Deleted interaction '{interaction_id}' from Firebase 'messages'.")


        # --- Deleting from Alfred Files Metadata ---
        # This would require logic to remove entries from your alfred_files_metadata.json
        # and potentially the actual files. This is not implemented here to keep the focus on messages
        # and because it's a separate type of data store (local file vs. Firebase).
        # Example for metadata.json if beforeDate was applicable:
        # if os.path.exists(METADATA_FILE_PATH):
        #     with open(METADATA_FILE_PATH, 'r') as f:
        #         try:
        #             metadata = json.load(f)
        #             keys_to_delete = []
        #             for file_id, file_info in metadata.items():
        #                 uploaded_at_str = file_info.get("uploaded_at")
        #                 if uploaded_at_str:
        #                     try:
        #                         uploaded_at = datetime.fromisoformat(uploaded_at_str)
        #                         if uploaded_at.tzinfo is None:
        #                             uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)
        #                         if before_date and uploaded_at < before_date:
        #                             keys_to_delete.append(file_id)
        #                     except ValueError:
        #                         logger.warning(f"Skipping file metadata with malformed timestamp: {uploaded_at_str}")
        #             for key in keys_to_delete:
        #                 # Add logic to delete actual file too if desired
        #                 # os.remove(os.path.join(UPLOAD_FOLDER, key))
        #                 del metadata[key]
        #                 deleted_count += 1 # If counting file deletions
        #             with open(METADATA_FILE_PATH, 'w') as f:
        #                 json.dump(metadata, f, indent=4)
        #         except json.JSONDecodeError:
        #             logger.warning("Metadata file corrupted, cannot delete entries.")


        logger.info(f"Activity log clear operation completed. {deleted_count} records (interactions) deleted from messages collection.")
        return jsonify({
            "message": "Log de atividades limpo com sucesso.",
            "deletedCount": deleted_count
        }), 200

    except Exception as e:
        logger.error(f"Error clearing activities: {e}")
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


# --- Funções Auxiliares para Interação com Docker ---
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

# --- Endpoints ---

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

    if platform not in ['discord', 'telegram']:
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

# Helper function to format file sizes (reused from upload endpoint)
def format_bytes(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# Helper function to determine file type (basic example)
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


# Rota de callback: deve bater exatamente com o que está no Portal
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

# Roda o app quando executado diretamente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4959)















    