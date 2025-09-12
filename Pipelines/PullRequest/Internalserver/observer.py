import os
import hmac
import hashlib
import time
import requests
import subprocess
import shutil
import asyncio
import logging
from flask import Flask, request, abort
from dotenv import load_dotenv
import threading
import json

from firebase_admin import credentials, initialize_app, storage, db, delete_app

from PrGen import PrGen 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), "keys.env"))
app = Flask(__name__)
GITHUB_SECRET = os.getenv('GITHUB_SECRET', '')
repo_name = os.getenv('repo_name', '')
GITHUB_TOKEN = os.getenv('github_token', '')
repo_path = os.getenv('repo_path', '')
new_name_for_html = os.getenv('new_name_for_html', '')
new_name_for_js = os.getenv('new_name_for_js', '')
new_name_for_css = os.getenv('new_name_for_css', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

from Keys.FirebaseAppKeys import *
app1 = init_firebase()

@app.route('/webhook', methods=['POST'])
def webhook():
    if not verify_signature(request):
        abort(403, 'Assinatura inválida')

    payload = request.get_json()
    logger.info(f"Payload recebido: {payload.get('action')}")

    if (payload.get("action") == "closed"
            and payload["pull_request"]["merged"] is True
            and payload["pull_request"]["base"]["ref"] == "main"):

        logger.info("Pull request mesclado na main. Iniciando deploy...")

        try:


            def minha_funcao():
                repo_path2 = "/app/Employers-AI-Support"
                if os.path.exists(repo_path2):
                    logger.info(f"Removendo repositório existente em {repo_path2}")

                    force_remove(repo_path2)
                # Clona repositório
                clone_url = f"https://github.com/ualers2/Employers-AI-Support.git"
                logger.info(f"Clonando repositório: {clone_url}")
                subprocess.run(["git", "clone", clone_url, repo_path2], check=True)

                time.sleep(5)
                # path = os.path.join("/app")
                # logger.info(f"path? {path}")
                deploy_containers()
            thread = threading.Thread(target=minha_funcao)
            thread.start()

            logger.info("Build e containerização do backend concluídos com sucesso (detached).")

            logger.info("Deploy concluído com sucesso.")
            return 'Atualização concluída', 200

        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar subprocesso: {e}")
            return 'Erro no deploy', 500
        except Exception as e:
            logger.exception(f"Erro inesperado: {e}")
            return 'Erro inesperado', 500

    logger.info("Evento ignorado.")
    return 'Evento ignorado', 200

@app.route('/webhook/genpr', methods=['POST'])
def webhookgenpr():
    if not verify_signature(request):
        abort(403, 'Assinatura inválida')

    payload = request.get_json()
    event_type = request.headers.get('X-GitHub-Event')
    logger.info(f"Payload recebido: {payload.get('action')}, Evento: {event_type}")
    if event_type == "pull_request":
        action = payload.get("action")
        pull_request = payload.get("pull_request")
        if action in ["opened", "reopened", "synchronize"] and pull_request:
            pr_url = pull_request["url"]
            pr_diff_url = pull_request["diff_url"]
            pr_number = pull_request["number"]
            pr_title = pull_request["title"]
            pr_body = pull_request["body"]
            logger.info(f"Evento de Pull Request '{action}' recebido para PR #{pr_number}")
            threading.Thread(target=process_pull_request, args=(pr_url, pr_diff_url, pr_number, pr_title, pr_body)).start()
            return 'Processamento do Pull Request iniciado', 202

    logger.info("Evento ignorado.")
    return 'Evento ignorado', 200

def main():
    update_repo(repo_path)
    time.sleep(2)
    deploy_containers()
    
def merge_pull_request(pr_number: int):
    merge_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/merge"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        "merge_method": "merge",  # Pode ser "merge", "squash" ou "rebase"
        "commit_title": f"Auto-merge PR #{pr_number}",
        "commit_message": "Merge automático realizado pelo agente"
    }
    response = requests.put(merge_url, headers=headers, json=data)
    
    if response.status_code == 200:
        logger.info(f"PR #{pr_number} mesclado com sucesso.")
    else:
        logger.error(f"Falha ao tentar mergear PR #{pr_number}: {response.text}")

def fetch_pr_diff_via_api(pr_api_url: str, token: str) -> str:
    # pr_api_url deve ser: https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Employers-AI-Support-Automation',
    }
    response = requests.get(pr_api_url, headers=headers, timeout=120)
    response.raise_for_status()
    
    files = response.json()
    diff_parts = []
    for f in files:
        if 'patch' in f:
            diff_parts.append(f"--- {f['filename']}\n{f['patch']}")
    return "\n".join(diff_parts)

def reset_all_users_tasks():
    """
    Reseta as tarefas de todos os usuários antes da build/deploy.
    Também percorre a fila e redefine status 'Running' para 'PENDING'.
    """
    try:
        root_ref = db.reference('Users_Control_Panel', app=app1)
        users_data = root_ref.get()

        shortify_queue_ref = db.reference('shortify_queue', app=app1)
        queue_data = shortify_queue_ref.get()

        # Reset dos usuários
        if users_data:
            for api_key, data in users_data.items():
                user_ref = db.reference(f'Users_Control_Panel/{api_key}', app=app1)
                user_ref.update({
                    'projects_running': 0,
                })
            logger.info("✅ Todas as tarefas dos usuários foram resetadas com sucesso.")
        else:
            logger.info("Nenhum usuário encontrado para resetar tarefas.")

        # Reset da fila (shortify_queue)
        if queue_data:
            for task_id, task in queue_data.items():
                if task.get("status") == "Running":
                    task_ref = shortify_queue_ref.child(task_id)
                    task_ref.update({"status": "PENDING"})
                    logger.info(f"🔄 Tarefa {task_id} alterada de Running para PENDING.")
            logger.info("✅ Todas as tarefas em execução foram redefinidas para PENDING.")
        else:
            logger.info("Nenhum queue encontrado para resetar tarefas.")

    except Exception as e:
        logger.error(f"Erro ao resetar tarefas dos usuários: {e}")

def process_pull_request(pr_url, pr_diff_url, pr_number, pr_title, current_pr_body):
    try:
        logger.info(f"DEBUG: reset all users tasks") 
        reset_all_users_tasks()
        files_api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/files"
        diff_content = fetch_pr_diff_via_api(files_api_url, GITHUB_TOKEN)
        logger.info(f"DEBUG: pr_diff_url original do payload: {pr_diff_url}") 
        logger.info(f"Diff obtido para PR #{pr_number}")
        logger.info(f"Diff content #{diff_content}")
        title, generated_pr_content = asyncio.run(PrGen(content_pr=diff_content, model="gpt-5-nano"))
        if title == "" or title == None:
            title = "Sem Titulo"
        logger.info(f"Conteúdo do PR gerado para PR #{pr_number}")
        update_pr_body(pr_url, title, generated_pr_content)
        merge_pull_request(pr_number)
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao buscar diff para PR #{pr_number}: {e}")
    except Exception as e:
        logger.exception(f"Erro inesperado no processamento do PR #{pr_number}: {e}")

def update_pr_body(pr_api_url, title, new_body):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'title': title, # Manter o título existente
        'body': new_body
    }
    response = requests.patch(pr_api_url, headers=headers, json=data)
    response.raise_for_status()
    logger.info(f"Corpo do Pull Request atualizado para {pr_api_url}")

def force_remove(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
    os.chmod(path, 0o777)
    shutil.rmtree(path)

def copy_filess(origin, destin):

    try:
            
        shutil.copy(origin, destin)
    except Exception as er1:
        try:
            shutil.copy2(origin, destin)
        except Exception as er2:
            try:
                shutil.copyfile(origin, destin)
            except Exception as er3:
                logger.info(er3)

def verify_signature(req):
    sig_header = req.headers.get('X-Hub-Signature-256')
    if sig_header is None:
        logger.warning("Cabeçalho de assinatura ausente.")
        return False
    try:
        sha_name, sig_hex = sig_header.split('=')
    except ValueError:
        logger.warning("Formato inválido da assinatura.")
        return False
    if sha_name != 'sha256':
        logger.warning("Algoritmo de hash incorreto.")
        return False
    mac = hmac.new(GITHUB_SECRET.encode(), msg=req.data, digestmod=hashlib.sha256)
    is_valid = hmac.compare_digest(mac.hexdigest(), sig_hex)
    if not is_valid:
        logger.warning("Assinatura inválida.")
    return is_valid

def update_repo(path):
    clone_url = f"https://{GITHUB_TOKEN}@github.com/{repo_name}.git"
    if not os.path.exists(path):
        # Primeiro clone, já com token
        subprocess.run(["git", "clone", clone_url, path], check=True)
    else:
        # Ajusta a URL do remote origin para incluir o token
        subprocess.run(["git", "-C", path, "remote", "set-url", "origin", clone_url], check=True)
        # Sincroniza sem manter alterações locais
        subprocess.run(["git", "-C", path, "fetch", "origin"], check=True)
        subprocess.run(["git", "-C", path, "checkout", "main"], check=True)
        subprocess.run(["git", "-C", path, "reset", "--hard", "origin/main"], check=True)

def deploy_containers():
    time.sleep(5)

    

    path = os.path.join("/app/Employers-AI-Support")
    logger.info(f"path? {path}")

    # logger.info("Copy Employers-AI-Support")


    logger.info("Copy .env")
    vite_config_ts_origin = os.path.join(os.path.dirname(__file__), "Production", 'Front-End', ".env")
    vite_config_ts_destin = os.path.join(os.path.dirname(__file__), "Employers-AI-Support", 'Front-End', ".env")

    copy_filess(vite_config_ts_origin, vite_config_ts_destin)

    logger.info("Copy Keys")

    EmployersAISupport_path_Keys_origin = os.path.join(os.path.dirname(__file__),  "Production", 'Back-End', 'Keys')
    EmployersAISupport_path_Keys_destin = os.path.join(os.path.dirname(__file__), "Employers-AI-Support", 'Back-End',  'Keys')

    try:
        if os.path.exists(EmployersAISupport_path_Keys_destin):
            shutil.rmtree(EmployersAISupport_path_Keys_destin)  
        shutil.copytree(EmployersAISupport_path_Keys_origin, EmployersAISupport_path_Keys_destin)
    except Exception as e:
        logger.error(f"Erro ao copiar diretório: {e}")

    logger.info("Copy docker-compose.yml")
    docker_compose_origin = os.path.join(os.path.dirname(__file__), "Production", "docker-compose.yml")
    docker_compose_destin = os.path.join(os.path.dirname(__file__), "Employers-AI-Support", "docker-compose.yml")

    copy_filess(docker_compose_origin, docker_compose_destin)

    logger.info("Copy vite.config.ts")
    docker_compose_origin = os.path.join(os.path.dirname(__file__), "Production", "Front-End", "vite.config.ts")
    docker_compose_destin = os.path.join(os.path.dirname(__file__), "Employers-AI-Support", "Front-End", "vite.config.ts")

    copy_filess(docker_compose_origin, docker_compose_destin)


    up_service("frontend_support", path)
    up_service("api_support", path)
    # up_service("telegram", path)
    # up_service("discord", path)
    # up_service("whatsapp", path)
    up_service("evolution-api", path)
    up_service("meu_postgres", path)


def wait_container_running(service_name, cwd, timeout=120, interval=2):
    """
    Espera até que o container <service_name> do Docker Compose esteja 'running'.
    Retorna True se virou running antes do timeout, False caso contrário.
    """
    start = time.time()
    while time.time() - start < timeout:
        # 1) Pega o ID do container
        cmd_ps = ["docker", "compose", "ps", "-q", service_name]
        result = subprocess.run(cmd_ps, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        container_id = result.stdout.decode().strip()
        if container_id:
            # 2) Inspeciona o status
            cmd_inspect = ["docker", "inspect", container_id, "--format", "{{json .State.Status}}"]
            out = subprocess.run(cmd_inspect, stdout=subprocess.PIPE)
            status = json.loads(out.stdout.decode().strip())
            if status == "running":
                return True
        time.sleep(interval)
    return False

def down_service(service_name, cwd):
    subprocess.Popen([
        "docker", "compose", "--compatibility", "stop", service_name
    ], cwd=cwd).wait()

def up_service(service_name, cwd):
    subprocess.Popen([
        "docker", "compose", "--compatibility", "up", "--build", "-d", service_name
    ], cwd=cwd)

if __name__ == '__main__':
    logger.info("Inicialized !!!!!!")
    app.run(host='0.0.0.0', port=5094)
