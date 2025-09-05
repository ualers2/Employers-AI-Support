import requests

def download_(UPLOAD_URL, save_path, PROJECT_NAME, VIDEO_ID, USER_ID_FOR_TEST) -> str:
    """
    Faz o download de um vídeo usando o endpoint otimizado de performance.
    Endpoint: /api/projects/<project_name>/videos/<video_id>/download

    Args:
        UPLOAD_URL (str): URL base do servidor Flask
        save_path (str): Caminho local para salvar o arquivo
        PROJECT_NAME (str): Nome do projeto
        VIDEO_ID (str): ID do vídeo
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

            # Grava em disco apenas chunks não vazios
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Falha ao baixar vídeo: {e}") from e

    return save_path

if __name__ == '__main__':
    UPLOAD_URL = "https://videomanager.api.mediacutsstudio.com"
    USER_ID_FOR_TEST = "freitasalexandre810@gmail.com"
    save_path = r"C:\Users\Media Cuts DeV\Downloads\HomeServer\HomeServer\internalsheduleserver\Internal-server\Modules\token.pickle"
    PROJECT_NAME = "cortesdofelquinhasss"
    VIDEO_ID = "04120ccf-8098-4388-b01f-76179beec198"
    download_(UPLOAD_URL, save_path, PROJECT_NAME, VIDEO_ID, USER_ID_FOR_TEST)