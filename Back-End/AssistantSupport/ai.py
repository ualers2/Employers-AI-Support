# Back-End\AssistantSupport\ai.py
from agents import Agent, handoff, RunContextWrapper, Runner
import requests
from dotenv import load_dotenv, find_dotenv
import os
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel
import logging

from api import app
from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus
from Modules.FileServer.download_ import download_

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Alfred:
    """
    Alfred é o primeiro agente softwareai a entrar na força de trabalho da compania,
    o agente substitui a contratação de humanos para o suporte de duvidas 
    e problemas dos usuarios , 
    o agente pode ser inferido pelo usuario via `telegram` e `discord` e `WhatsApp`

    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
       
        # self.app_1 = app_1
        # self.alfred_files_metadata_ref = db.reference('alfred_knowledge_metadata', app=app_1)
     
        self.nameAlfred = "Alfred"
        self.model_selectAlfred = "gpt-5-nano"
        self.adxitional_instructions_Alfred = ""
        self.system_ = "siga com os objetivos da instrucao"
        self.instruction_db = """
        ## Objetivo        Oferecer suporte completo aos usuários do **Media Cuts Studio**, garantindo a resolução rápida de problemas, registro organizado de tickets, e coleta de feedback para melhoria contínua.
        """
        self.logger.info(self.nameAlfred)
        self.logger.info(self.model_selectAlfred)
        self.logger.info(self.instruction_db)

        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../', 'Keys', 'keys.env'))

        self.UPLOAD_URL_VIDEOMANAGER = os.getenv("UPLOAD_URL")
        self.project_name = os.getenv("Employers_AI_Support")
        self.USER_ID_FOR_TEST = os.getenv("USER_ID_FOR_TEST")

    # def get_alfred_local_file_paths(self):
    #     """
    #     Percorre todos os nós da referência 'alfred_knowledge_metadata' no Firebase,
    #     obtém o 'local_path' de cada arquivo e retorna uma lista desses caminhos.
    #     Ignora entradas sem 'local_path' ou onde o arquivo não existe mais localmente.
    #     """
    #     try:
    #         # Pega todos os metadados da referência alfred_knowledge_metadata
    #         all_metadata = self.alfred_files_metadata_ref.get()

    #         if not all_metadata:
    #             self.logger.info("Nenhum metadado de arquivo encontrado no Firebase para Alfred.")
    #             return []

    #         local_paths = []
    #         for file_id, metadata in all_metadata.items():
    #             if not isinstance(metadata, dict):
    #                 self.logger.warning(f"Metadado malformado para '{file_id}' no Firebase. Ignorando.")
    #                 continue

    #             local_path = metadata.get("local_path")

    #             if local_path:
    #                 # Opcional: Verifique se o arquivo realmente existe no disco
    #                 if os.path.exists(local_path):
    #                     local_paths.append(local_path)
    #                 else:
    #                     self.logger.warning(f"Arquivo local não encontrado para '{file_id}' no caminho: '{local_path}'. A entrada do Firebase pode estar desatualizada.")
    #                     # Opcional: Você pode querer remover essa entrada do Firebase se o arquivo não existe mais
    #                     # alfred_files_metadata_ref.child(file_id).delete()
    #             else:
    #                 self.logger.warning(f"Entrada de metadado para '{file_id}' no Firebase não possui 'local_path'. Ignorando.")

    #         self.logger.info(f"Retornados {len(local_paths)} caminhos de arquivos locais para Alfred.")
    #         return local_paths

    #     except Exception as e:
    #         self.logger.error(f"Erro ao obter caminhos de arquivos locais para Alfred: {e}", exc_info=True)
    #         return []
        
    def get_user_file_paths(self, user_identifier):
        """
        Retorna apenas os arquivos do usuário (não todos do banco).
        O user_identifier pode ser id (int) ou email (str).
        """
        try:
            with app.app_context():
                # 🔹 Resolver user_identifier (email ou id) para sempre virar user_id
                if isinstance(user_identifier, int) or str(user_identifier).isdigit():
                    user = User.query.get(int(user_identifier))
                else:
                    user = User.query.filter_by(email=user_identifier).first()

                if not user:
                    self.logger.info(f"Usuário '{user_identifier}' não encontrado.")
                    return []

                # Buscar arquivos pelo uploaded_by_user_id
                files = AlfredFile.query.filter_by(uploaded_by_user_id=user.id).all()
                if not files:
                    self.logger.info(f"Nenhum arquivo encontrado para usuário {user.id} ({user.email})")
                    return []

                local_paths = []
                for f in files:
                    file_id  = f.file_id
                    unique_filename = f.unique_filename
                    save_path = os.path.join(os.path.dirname(__file__), "../", "Knowledge", f"{unique_filename}")
                    local_path = download_(self.UPLOAD_URL_VIDEOMANAGER, save_path, self.project_name, file_id, self.USER_ID_FOR_TEST)
                    if local_path and os.path.exists(local_path):
                        local_paths.append(local_path)
                    else:
                        self.logger.warning(f"Arquivo não encontrado no disco: {f.local_path}")

                self.logger.info(f"Retornados {len(local_paths)} arquivos para o usuário {user.id} ({user.email})")
                return local_paths

        except Exception as e:
            self.logger.error(f"Erro ao buscar arquivos do usuário {user_identifier}: {e}", exc_info=True)
            return []
        
    async def Alfred(self, mensagem, user_platform_id):
        all_paths = self.get_user_file_paths(user_platform_id)
        all_content = ""
        for path in all_paths:
            file_extension = path.rsplit('.', 1)[1].lower() if '.' in path else ''
            if file_extension in {'md', 'txt', 'csv', 'json'}:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        all_content += content + "\n\n--- FIM DO ARQUIVO ---\n\n" # Adicionar um separador
                except Exception as e:
                    # Logar ou lidar com erros de leitura de arquivo (permissão, corrupção, etc.)
                    print(f"Erro ao ler arquivo de texto {path}: {e}")
            # elif file_extension == 'pdf':
            #     # Implementar lógica para extrair texto de PDF
            #     print(f"Implementar extração de texto para PDF: {path}")
            #     from PyPDF2 import PdfReader
            #     reader = PdfReader(path)
            #     for page in reader.pages:
            #         all_content += page.extract_text() + "\n"
        self.logger.info(all_content)
        self.instruction = f"""
        **Contexto e informacoes:**  
        Aqui voce encontra Contexto e informacoes do aplicativo 
        {all_content}

        ---
        {self.instruction_db}

        """
        # Tools_Name_dict = Egetoolsv2(list(tools_agent))
        agent = Agent(
            name=self.nameAlfred,
            instructions =self.instruction,
            model=self.model_selectAlfred,
            # tools=Tools_Name_dict,
        )

        result = await Runner.run(agent, mensagem, max_turns=300)
        raw_ = result.final_output
        print(raw_)


        return raw_

    