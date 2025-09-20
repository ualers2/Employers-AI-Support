# Back-End\test_client_chat.py
from agents import Agent, ItemHelpers, Runner, RunHooks, handoff, ModelSettings, RunConfig, RunContextWrapper, Usage
import logging
import os
from firebase_admin import db
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel, Field
from openai.types.responses import ResponseCompletedEvent, ResponseTextDeltaEvent
import requests
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dotenv import load_dotenv
from Modules.FileServer.upload_ import upload_
from Modules.FileServer.download_ import download_

# from Modules.Services.Geters.user_file_paths import get_user_file_paths
from Agents.ClientChat.ai import _load_company_documents

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'Keys', 'keys.env'))
# Documentos da empresa para contexto
company_documents = {
    "manifesto": "d3cdce8c-83e9-48ce-9999-a9f03b8b27c3",
    "limitacoes": "cc5915a2-2b5b-4a97-945e-d89efa6ec674", 
    "Perguntas": "7c46cb7e-6b3f-4e1c-8d81-0856caf6c492",
    "Informacoes": "9d5a06f4-76f9-4920-8ba2-dcd20e29f5bc"
}

filenames = [
    "Manifesto da Marca.md",
    "Limitações de Conta do Usuário.md", 
    "Perguntas Frequentes.md",
    "Informações Técnicas.md"
]
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "storage")
UPLOAD_URL = os.getenv("UPLOAD_URL")
USER_ID = os.getenv("USER_ID_FOR_TEST")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Download e processamento dos documentos
contents = asyncio.run(_load_company_documents(
    company_documents, filenames, UPLOAD_FOLDER, UPLOAD_URL, USER_ID
))



