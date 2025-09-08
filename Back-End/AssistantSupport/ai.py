
from agents import Agent, handoff, RunContextWrapper, Runner
import requests
from dotenv import load_dotenv, find_dotenv
import os
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel
import logging
from firebase_admin import db


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Alfred:
    """
    Alfred é o primeiro agente softwareai a entrar na força de trabalho da compania,
    o agente substitui a contratação de humanos para o suporte de duvidas 
    e problemas dos usuarios , 
    o agente pode ser inferido pelo usuario via `telegram` e `discord` e `WhatsApp`

    """
    def __init__(self, app_1):
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
       
        self.app_1 = app_1
        self.alfred_files_metadata_ref = db.reference('alfred_knowledge_metadata', app=app_1)
        self.alfred_ref = db.reference('configurations', app=app_1)
        data = self.alfred_ref.get()
        
        self.nameAlfred = data.get("alfredName", "Alfred")
        self.model_selectAlfred = data.get("alfredModel", "gpt-4.1-nano")
        self.adxitional_instructions_Alfred = ""
        self.system_ = "siga com os objetivos da instrucao"

        self.instruction_db = data.get("alfredInstructions", "")
        self.logger.info(self.nameAlfred)
        self.logger.info(self.model_selectAlfred)
        self.logger.info(self.instruction_db)

        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../', 'Keys', 'keys.env'))

                

    def get_alfred_local_file_paths(self):
        """
        Percorre todos os nós da referência 'alfred_knowledge_metadata' no Firebase,
        obtém o 'local_path' de cada arquivo e retorna uma lista desses caminhos.
        Ignora entradas sem 'local_path' ou onde o arquivo não existe mais localmente.
        """
        try:
            # Pega todos os metadados da referência alfred_knowledge_metadata
            all_metadata = self.alfred_files_metadata_ref.get()

            if not all_metadata:
                self.logger.info("Nenhum metadado de arquivo encontrado no Firebase para Alfred.")
                return []

            local_paths = []
            for file_id, metadata in all_metadata.items():
                if not isinstance(metadata, dict):
                    self.logger.warning(f"Metadado malformado para '{file_id}' no Firebase. Ignorando.")
                    continue

                local_path = metadata.get("local_path")

                if local_path:
                    # Opcional: Verifique se o arquivo realmente existe no disco
                    if os.path.exists(local_path):
                        local_paths.append(local_path)
                    else:
                        self.logger.warning(f"Arquivo local não encontrado para '{file_id}' no caminho: '{local_path}'. A entrada do Firebase pode estar desatualizada.")
                        # Opcional: Você pode querer remover essa entrada do Firebase se o arquivo não existe mais
                        # alfred_files_metadata_ref.child(file_id).delete()
                else:
                    self.logger.warning(f"Entrada de metadado para '{file_id}' no Firebase não possui 'local_path'. Ignorando.")

            self.logger.info(f"Retornados {len(local_paths)} caminhos de arquivos locais para Alfred.")
            return local_paths

        except Exception as e:
            self.logger.error(f"Erro ao obter caminhos de arquivos locais para Alfred: {e}", exc_info=True)
            return []

    async def Alfred(self, mensagem):

        all_paths = self.get_alfred_local_file_paths()
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
            elif file_extension == 'pdf':
                # Implementar lógica para extrair texto de PDF
                print(f"Implementar extração de texto para PDF: {path}")
                from PyPDF2 import PdfReader
                reader = PdfReader(path)
                for page in reader.pages:
                    all_content += page.extract_text() + "\n"
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

    