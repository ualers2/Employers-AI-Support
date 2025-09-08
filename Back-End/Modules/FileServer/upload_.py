"""
Módulo de upload de arquivos e vídeos
-------------------------------------

Este módulo é responsável por realizar o upload de arquivos para um servidor Flask
configurado via variável de ambiente `UPLOAD_URL`.  
Também realiza o gerenciamento de logs, registrando informações sobre sucesso, falha
e exceções durante o processo de envio.

Funcionalidades principais:
- Configuração de logging (arquivo e console).
- Carregamento de variáveis de ambiente a partir de `keys.env`.
- Upload de arquivos com metadados de projeto para a API de backend.

Extensões de arquivo permitidas:
    - Vídeos: mp4
    - Legendas / dados: srt, ass, pickle, json
    - Áudio: wav
    - Imagens: jpg, jpeg, png, gif, webp, bmp
    - Frontend (React + Vite): js, jsx, ts, tsx, html, css, svg, ico
    - Configurações e documentos: md, pdf
    - Python: py
"""

import os
import json
from dotenv import load_dotenv, find_dotenv
import requests
import logging


diretorio_script = os.path.dirname(__file__) 
os.makedirs(os.path.join(diretorio_script, '../', 'Logs'), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(os.path.join(diretorio_script, '../', 'Logs', 'upload_py.log'))
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def upload_(name_project, VIDEO_FILE_PATH, USER_ID_FOR_TEST):
    """
    Realiza o upload de um vídeo ou arquivo para o servidor.

    Args:
        name_project (str): Nome do projeto associado ao vídeo.
        VIDEO_FILE_PATH (str): Caminho absoluto ou relativo para o arquivo MP4 a ser enviado.
        USER_ID_FOR_TEST (str): ID do usuário geralmente email (passado no header `X-User-Id`).

    Returns:
        str | None: Retorna o `video_id` fornecido pelo servidor em caso de sucesso,
        ou `None` caso o upload falhe.

    Comportamento:
        - Lê as variáveis de ambiente do arquivo `.env` se `UPLOAD_URL` não estiver configurado.
        - Envia o arquivo MP4 via POST para `{UPLOAD_URL}/api/upload-video`.
        - Inclui metadados com nome e tipo do projeto.
        - Registra logs em console e arquivo (`Logs/upload_py.log`).
        - Trata erros de arquivo inexistente, conexão recusada ou falhas inesperadas.

    Exemplo:
        >>> upload_("MeuProjeto", "./video.mp4", "12345")
        'abcde12345idvideo'
    """
    UPLOAD_URL = os.getenv("UPLOAD_URL")
    if UPLOAD_URL == None:
        load_dotenv(os.path.join(diretorio_script, '../', '../', 'Keys', 'keys.env'))
        UPLOAD_URL = os.getenv("UPLOAD_URL")

    video_metadata = {
        "projectName": name_project,
        "type_project": "files",

    }

    if not os.path.exists(VIDEO_FILE_PATH):
        logger.info(f"Erro: O arquivo '{VIDEO_FILE_PATH}' não foi encontrado.")
        logger.info("Por favor, crie um arquivo MP4 com este nome ou ajuste o caminho.")
        exit()

    try:
        with open(VIDEO_FILE_PATH, 'rb') as video_file:
            files = {
                'file': (os.path.basename(VIDEO_FILE_PATH), video_file, 'video/mp4')
            }
            data = {
                'metadata': json.dumps(video_metadata)
            }
            headers = {
                'X-User-Id': USER_ID_FOR_TEST 
            }
            logger.info(f"Tentando enviar '{VIDEO_FILE_PATH}' para {UPLOAD_URL}...")
            logger.info(f"Com metadados: {json.dumps(video_metadata, indent=2)}")
            response = requests.post(F"{UPLOAD_URL}/api/upload-video", files=files, data=data, headers=headers)

            if response.status_code == 201 or response.status_code == 200:
                logger.info("\nUpload bem-sucedido!")
                logger.info("Resposta do servidor:")
                logger.info(json.dumps(response.json(), indent=2))
                payload = response.json()
                ID = payload['video_id']
                logger.info(f"ID: {ID}")
                return ID
            else:
                logger.info(f"\nErro no upload: Código de status {response.status_code}")
                logger.info("Resposta do servidor:")
                try:
                    logger.info(json.dumps(response.json(), indent=2))
                except json.JSONDecodeError:
                    print(response.text) 
                logger.info("\nCertifique-se de que seu servidor Flask está rodando e o endpoint está acessível.")
                logger.info("Verifique também se o 'USER_ID_FOR_TEST' e o 'UPLOAD_URL' estão corretos.")

    except FileNotFoundError:
        logger.info(f"Erro: O arquivo '{VIDEO_FILE_PATH}' não foi encontrado.")
    except requests.exceptions.ConnectionError:
        logger.info("Erro de conexão: O servidor não está acessível.")
        logger.info("Certifique-se de que o backend Flask está rodando em 'http://localhost:5000'.")
    except Exception as e:
        logger.info(f"Ocorreu um erro inesperado: {e}")
