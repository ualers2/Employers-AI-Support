# Back-End\AssistantSupport\ai.py
from agents import Agent, handoff, RunContextWrapper, Runner, SQLiteSession
import requests
from dotenv import load_dotenv, find_dotenv
import os
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel
import logging
from datetime import datetime  # 🔹 para registrar o last_update
from sqlalchemy.exc import IntegrityError

# from api import app
from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus
from Modules.FileServer.download_ import download_
from Modules.Functions.TicketProblem import *

from Modules.Services.Geters.user_file_paths import get_user_file_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Alfred:
    """
    Alfred é o primeiro agente softwareai a entrar na força de trabalho da compania,
    o agente substitui a contratação de humanos para o suporte de duvidas 
    e problemas dos usuarios , 
    o agente pode ser inferido pelo usuario via `telegram` e `discord` e `WhatsApp`

    """
    def __init__(self, app):
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.app = app
        self.nameAlfred = "Alfred"
        self.model_selectAlfred = "gpt-5-nano"
        self.adxitional_instructions_Alfred = ""
        self.system_ = "siga com os objetivos da instrucao"

        self.logger.info(self.nameAlfred)
        self.logger.info(self.model_selectAlfred)
        # self.logger.info(self.instruction_db)

        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../', 'Keys', 'keys.env'))

        self.UPLOAD_URL_VIDEOMANAGER = os.getenv("UPLOAD_URL")
        self.project_name = os.getenv("Employers_AI_Support")
        self.USER_ID_FOR_TEST = os.getenv("USER_ID_FOR_TEST")
        self.AGENT_PLATFORM = "alfred" 

    def Alfred(self, mensagem, user_platform_id, conversation_id, platform="telegram"):
        self.register_status(user_platform_id, platform)
        all_paths = get_user_file_paths(self.app, user_platform_id, 
                        self.UPLOAD_URL_VIDEOMANAGER,
                        self.project_name,
                        self.USER_ID_FOR_TEST
                    )
        all_content = ""
        for path in all_paths:
            file_extension = path.rsplit('.', 1)[1].lower() if '.' in path else ''
            if file_extension in {'md', 'txt', 'csv', 'json'}:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        all_content += content + "\n\n--- FIM DO ARQUIVO ---\n\n" # Adicionar um separador
                except Exception as e:
                    print(f"Erro ao ler arquivo de texto {path}: {e}")
         
        self.logger.info(all_content)
        self.instruction_db = f"""
## Objetivos e Regras       
Objetivo: Oferecer suporte completo aos usuários, garantindo a resolução rápida de problemas, registro organizado de tickets, e coleta de feedback para melhoria contínua 
Regras:
- voce deve agir naturalmente assim como um humano no dia a dia evitando textos extremamente longos (pois os usuarios tem preguiça de ler e tambem escrever) ou palavras de dificil entendimento 
- voce deve agir como um humano de suporte ao cliente

## Criterios
- utilize a ferramenta OpenSupportTicketProblem de forma pro ativa abrindo um ticket para a equipe tecnica sempre que indentificar um problema 
- sempre apos a abertura de um ticket informe que a equipe tecnica ja foi notificada e tente coletar mais 1 ou 3 informacoes a mais do problema (para nao cansar o usuario) utilizando a ferramenta AddTicketNote


Detalhes:\n


# ### **Detalhes do OpenSupportTicketProblem:**  
# - **user_email:** email ou id do usuario: {user_platform_id} (nao use nada alem do id ou email nem peça ao usuario)
# - **issue_description:** descricao do problema do usuario
\n

# ### **Detalhes do AddTicketNote:**  
# - **ticketid:** id do ticket (nao peça ao usuario utilize id que foi aberto com OpenSupportTicketProblem)
# - **note_content:** informacoes a mais coletadas sobre o problema do usuario
\n

# ### **Detalhes do GetTicketDetails:**  
# - **ticketid:** id do ticket (nao peça ao usuario utilize id que foi aberto com OpenSupportTicketProblem)
\n

# ### **Detalhes do EscalateTicket:**  
# - **ticketid:** id do ticket (nao peça ao usuario utilize id que foi aberto com OpenSupportTicketProblem)
# - **reason:** a descricao detalhada do motivo da escalar o ticket 

\n
        """
        self.instruction = f"""

{self.instruction_db}
---

**Contexto e informacoes:**  
Aqui voce encontra Contexto e informacoes de documentos para conseguir entender e dar o melhor suporte
{all_content}

        """
        Tools_Name_dict = [OpenSupportTicketProblem, 
                           CloseSupportTicketProblem, 
                           RecordCSAT, 
                           GetTicketDetails,
                           EscalateTicket,
                           AddTicketNote
                           
                           ] 
                
        session = SQLiteSession(f"{conversation_id}", os.path.join(os.path.dirname(__file__), '../', '../', 'Knowledge', 'Db', 'conversations.db'))

        agent = Agent(
            name=self.nameAlfred,
            instructions =self.instruction,
            model=self.model_selectAlfred,
            tools=Tools_Name_dict,
        )

        result = Runner.run_sync(agent, mensagem, max_turns=300, session=session)
        raw_ = result.final_output
        logger.info(raw_)

        return raw_


    def register_status(self, user_platform_id, platform):
        """
        Registra ou atualiza o status do agente Alfred no banco.
        """
        try:
            with self.app.app_context():

                user = resolve_user_identifier(user_platform_id)
               
                numeric_user_id = user.id

                agent = AgentStatus.query.filter_by(user_id=numeric_user_id).first()

                metadata = {
                    "name": self.nameAlfred,
                    "area": "Suporte Ao Cliente",
                    "tasks": ["Responder usuários", "Abrir tickets", "Coletar feedback"],
                    "platform": f"{platform}",
                    "container_name": f"alfred-{platform}-agent",
                    "image_name": f"{platform}-server:latest",
                    "status": "online",
                }
                if agent:
                    agent.status = metadata.get('status')
                    agent.last_update = datetime.utcnow()

                    if agent.name == "Default Name":
                        agent.name = metadata.get('name')
                    if agent.area == "General":
                        agent.area = metadata.get('area')
                    if not agent.tasks or agent.tasks == []:
                        agent.tasks = metadata.get('tasks')
                    if not agent.platform:
                        agent.platform = metadata.get('platform')
                    if not agent.container_name:
                        agent.container_name = metadata.get('container_name')
                    if not agent.image_name:
                        agent.image_name = metadata.get('image_name')
                    
                else:
                    agent = AgentStatus(
                        user_id=numeric_user_id,
                        name=metadata.get('name'),
                        area=metadata.get('area'),
                        tasks=metadata.get('tasks'),
                        platform=metadata.get('platform'),
                        container_name=metadata.get('container_name'),
                        image_name=metadata.get('image_name'),
                        status=metadata.get('status'),
                        last_update=datetime.utcnow()
                    )
                    db.session.add(agent)

                db.session.commit()
                self.logger.info(f"Agente {self.nameAlfred} registrado/atualizado como {metadata.get('status')}")
        except IntegrityError as e:
            db.session.rollback()
            self.logger.error(f"Erro ao registrar agente: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado no registro de status: {e}")