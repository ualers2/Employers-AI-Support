"""
Módulo de download de vídeos
----------------------------

Este módulo fornece a função `download_` responsável por baixar vídeos ou arquivos
de um servidor Flask. O processo utiliza o endpoint otimizado de performance para 
streaming seguro e gravação em disco.

Funcionalidades principais:
- Monta a URL de download com base no nome do projeto e ID do vídeo.
- Envia cabeçalho de autenticação com `X-User-Id`.
- Faz streaming em chunks para evitar sobrecarga de memória.
- Lança exceções em caso de falha na requisição.
"""

import requests

def download_(UPLOAD_URL, save_path, PROJECT_NAME, VIDEO_ID, USER_ID_FOR_TEST) -> str:
    """
    Faz o download de um vídeo ou arquivo usando o endpoint otimizado de performance.
    Endpoint: /api/projects/<project_name>/videos/<video_id>/download

    Args:
        UPLOAD_URL (str): URL base do servidor Flask
        save_path (str): Caminho local para salvar o arquivo
        PROJECT_NAME (str): Nome do projeto
        VIDEO_ID (str): ID do vídeo ou arquivo
        USER_ID_FOR_TEST (str): ID do usuário autenticado (passado no header)

    Returns:
        str: Caminho local do arquivo baixado
    """
    url = f"{UPLOAD_URL}/api/projects/{PROJECT_NAME}/videos/{VIDEO_ID}/download"
    headers = {
        "X-User-Id": USER_ID_FOR_TEST,
    }

    try:
        with requests.get(url, headers=headers, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Falha ao baixar vídeo: {e}") from e

    return save_path
