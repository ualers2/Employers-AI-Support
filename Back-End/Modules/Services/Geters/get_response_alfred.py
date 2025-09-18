
import os
import logging
import uuid
import json
import re
import asyncio
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from typing import List, Dict
from datetime import datetime, timedelta, timezone
import requests 
import asyncio
import logging
from flask import request, jsonify
from typing import Dict, Any, Optional
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_response_alfred(
        user_id,
        plataform,
        session_id,
        url_base=''
        
        ):

    try:
        data = {
            'user_id': user_id,
            'plataform': plataform,
            'session_id': session_id

        }
        response = requests.post(F"{url_base}/api/alfred", json=data)

        if response.status_code == 201 or response.status_code == 200:
            logger.info("Resposta do servidor:")
            logger.info(json.dumps(response.json(), indent=2))
            payload = response.json()
            message = payload['message']
            logger.info(f"message: {message}")
            return message
        else:
            logger.info(f"\nErro no upload: Código de status {response.status_code}")
            logger.info("Resposta do servidor:")
            try:
                logger.info(json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                print(response.text) 
            logger.info("\nCertifique-se de que seu servidor Flask está rodando e o endpoint está acessível.")
            logger.info("Verifique também se o 'USER_ID_FOR_TEST' e o 'UPLOAD_URL' estão corretos.")

    except requests.exceptions.ConnectionError:
        logger.info("Erro de conexão: O servidor não está acessível.")
        logger.info("Certifique-se de que o backend Flask está rodando em 'http://localhost:5000'.")
    except Exception as e:
        logger.info(f"Ocorreu um erro inesperado: {e}")


