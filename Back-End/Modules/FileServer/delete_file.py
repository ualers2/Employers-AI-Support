# delete_file.py
import os
import json
import logging
from dotenv import load_dotenv
import requests

diretorio_script = os.path.dirname(__file__)
os.makedirs(os.path.join(diretorio_script, '../',  '../', 'Logs'), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(os.path.join(diretorio_script, '../',  '../', 'Logs', 'delete_video_py.log'))
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def delete_file(project_name: str, video_id: str, USER_ID_FOR_TEST: str, UPLOAD_URL: str = None, timeout: int = 15):
    """
    Solicita ao backend a exclusão de um vídeo/arquivo específico do projeto.

    Args:
        project_name (str): Nome do projeto (igual ao usado no upload).
        video_id (str): ID do vídeo/arquivo a ser excluído.
        USER_ID_FOR_TEST (str): ID do usuário (email) enviado no header 'X-User-Id'.
        UPLOAD_URL (str, opcional): URL base do servidor (ex: 'http://localhost:4242'). Se None, será carregado da env UPLOAD_URL.
        timeout (int): tempo limite em segundos para a requisição.

    Retorna:
        dict: JSON de resposta do servidor em caso de sucesso.
        None: em caso de falha (ver logs para detalhes).
    """
    if UPLOAD_URL is None:
        # tenta carregar da env (mesma lógica do upload_)
        load_dotenv(os.path.join(diretorio_script, '../', '../', 'Keys', 'keys.env'))
        UPLOAD_URL = os.getenv("UPLOAD_URL")
    if not UPLOAD_URL:
        logger.error("UPLOAD_URL não definido (nem por parâmetro, nem em env). Abortando.")
        return None

    # montar endpoint (não sanitizamos aqui pois o servidor já faz sua normalização)
    endpoint = f"{UPLOAD_URL.rstrip('/')}/api/projects/{project_name}/videos/{video_id}"

    headers = {
        "X-User-Id": USER_ID_FOR_TEST
    }

    try:
        logger.info(f"Tentando deletar vídeo '{video_id}' do projeto '{project_name}' em {endpoint}")
        resp = requests.delete(endpoint, headers=headers, timeout=timeout)

        try:
            payload = resp.json()
        except Exception:
            payload = {"text": resp.text}

        if resp.status_code == 200:
            logger.info("Exclusão bem-sucedida.")
            logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
            return payload
        elif resp.status_code == 401:
            logger.warning("Não autorizado (401). Verifique X-User-Id / autenticação.")
            logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
            return None
        elif resp.status_code == 404:
            logger.warning("Recurso não encontrado (404).")
            logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
            return None
        else:
            logger.error(f"Falha na requisição. Status: {resp.status_code}")
            logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
            return None

    except requests.exceptions.Timeout:
        logger.error("Timeout ao tentar conectar com o servidor.")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao solicitar exclusão: {e}")
        return None


if __name__ == "__main__":
    # exemplo de uso local
    UPLOAD_URL = "https://videomanager.api.mediacutsstudio.com"
    USER_ID_FOR_TEST = "freitasalexandre810@gmail_com"
    project = "8e0d14b8b9cc3f45"
    vid = "2394b4f3-12a8-4e62-82be-ca80f763fe54"

    result = delete_file(project, vid, USER_ID_FOR_TEST, UPLOAD_URL=UPLOAD_URL)
    print("Resultado:", result)
