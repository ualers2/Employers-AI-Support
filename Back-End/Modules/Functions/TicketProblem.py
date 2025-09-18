# Back-End\Functions\TicketProblem.py
import hashlib
from typing_extensions import TypedDict, Literal
from agents import function_tool
from datetime import datetime


from Modules.Services.Resolvers.user_identifier import resolve_user_identifier
from Modules.Models.postgressSQL import db, Ticket
from api import app

class GetTicketDetailsParams(TypedDict, total=False):
    ticketid: str

class OpenTicketParams(TypedDict, total=False):
    user_email: str 
    issue_description: str  

class CloseTicketParams(TypedDict, total=False):
    ticketid: str 

class EscalateTicketParams(TypedDict, total=False):
    ticketid: str
    reason: str 

class AddTicketNoteParams(TypedDict, total=False):
    ticketid: str
    note_content: str

class RecordCSATParams(TypedDict, total=False):
    ticketid: str 
    csat_score: str 

class GetUserInfoParams(TypedDict, total=False):
    user_email: str

class CheckSystemStatusParams(TypedDict, total=False):
    pass # Não precisa de parâmetros, verifica o status geral

class SuggestTroubleshootingStepsParams(TypedDict, total=False):
    issue_type: str # Categoria do problema (ex: "login", "desempenho", "pagamento")

class ScheduleCallbackParams(TypedDict, total=False):
    user_email: str
    preferred_datetime: str # Formato ISO 8601, ex: "2025-07-01T10:30:00"
    reason: str # Motivo do retorno de chamada

class GenerateReportParams(TypedDict, total=False):
    report_type: Literal["usage_history", "billing_summary", "performance_metrics"]
    user_email: str # Opcional, para relatórios específicos de usuário
    time_period: str # Ex: "last_month", "this_quarter", "2024-01-01_2024-03-31"

class CreateInternalTaskParams(TypedDict, total=False):
    summary: str # Resumo da tarefa
    description: str # Descrição detalhada
    priority: Literal["low", "medium", "high", "urgent"]
    assignee_team: str # Ex: "Engenharia", "Financeiro", "Vendas", "Produto"
    related_ticket_id: str # Opcional, ticket de suporte relacionado

@function_tool
def OpenSupportTicketProblem(params: OpenTicketParams):
    """
    Opens a new support ticket in the system.

    Args:
        params (OpenTicketParams): A dictionary containing:
            - user_email (str): The email of the user opening the ticket.
            - issue_description (str): A detailed description of the issue.

    Returns:
        str: A message confirming the ticket opening and its ID, e.g., "Open Ticket ID: abcde".
    """
    user_email = params.get("user_email")
    issue_description = params.get("issue_description")
    ticketid = hashlib.sha256(issue_description.encode("utf-8")).hexdigest()[:5]
    with app.app_context():
        user = resolve_user_identifier(user_email)
        if not user:
            return f"Usuário {user_email} não encontrado."

        ticket = Ticket(
            ticketid=ticketid,
            user_id=user.id,
            issue_description=issue_description,
        )
        db.session.add(ticket)
        db.session.commit()

    return f"Open Ticket ID: {ticketid}"

@function_tool
def CloseSupportTicketProblem(params: CloseTicketParams):
    """
    Closes an existing support ticket.

    Args:
        params (CloseTicketParams): A dictionary containing:
            - ticketid (str): The unique identifier of the ticket to close.

    Returns:
        str: A confirmation message, e.g., "Closed Ticket ID: abcde", or an error if the ticket is not found.
    """
    ticketid = params.get("ticketid")
    with app.app_context():
        ticket = Ticket.query.filter_by(ticketid=ticketid).first()

        if not ticket:
            return f"Ticket ID {ticketid} not found."

        ticket.status = "closed"
        ticket.timestamp_close = datetime.utcnow()
        db.session.commit()
    return f"Closed Ticket ID: {ticketid}"

@function_tool
def RecordCSAT(params: RecordCSATParams):
    """
    Records a Customer Satisfaction (CSAT) score for a given support ticket.

    Args:
        params (RecordCSATParams): A dictionary containing:
            - ticketid (str): The unique identifier of the ticket.
            - csat_score (str): The CSAT score to record (e.g., "1", "5", "Satisfied").

    Returns:
        str: A confirmation message, e.g., "CSAT registrado para o Ticket ID: abcde",
             or an error if the ticket is not found.
    """
    ticketid = params.get("ticketid")
    csat_score = params.get("csat_score")
    with app.app_context():
        ticket = Ticket.query.filter_by(ticketid=ticketid).first()
        if not ticket:
            return f"Ticket ID {ticketid} not found."

        ticket.csat = csat_score
        db.session.commit()
    return f"CSAT registrado para o Ticket ID: {ticketid}"

@function_tool
def GetTicketDetails(params: GetTicketDetailsParams):
    """
    Retrieves all details for a specific support ticket.

    Args:
        params (GetTicketDetailsParams): A dictionary containing:
            - ticketid (str): The unique identifier of the ticket.

    Returns:
        dict or str: A dictionary containing all ticket data if found,
                     or a string error message if the ticket is not found.
    """
    ticketid = params.get("ticketid")
    with app.app_context():
        ticket = Ticket.query.filter_by(ticketid=ticketid).first()

        if not ticket:
            return f"Ticket ID {ticketid} not found."

        return {
            "ticketid": ticket.ticketid,
            "user_email": ticket.user_email,
            "issue_description": ticket.issue_description,
            "status": ticket.status,
            "csat": ticket.csat,
            "notes": ticket.notes,
            "timestamp_open": ticket.timestamp_open.isoformat(),
            "timestamp_close": ticket.timestamp_close.isoformat() if ticket.timestamp_close else None,
            "timestamp_escalated": ticket.timestamp_escalated.isoformat() if ticket.timestamp_escalated else None,
            "escalation_reason": ticket.escalation_reason,
        }

@function_tool
def EscalateTicket(params: EscalateTicketParams):
    """
    Escalates a support ticket to a higher level or different department.
    This function marks the ticket as "escalated" and adds a reason.

    Args:
        params (EscalateTicketParams): A dictionary containing:
            - ticketid (str): The unique identifier of the ticket to escalate.
            - reason (str): The reason for escalating the ticket.

    Returns:
        str: A confirmation message, e.g., "Ticket ID abcde has been escalated for the following reason: ...",
             or an error if the ticket is not found.
    """
    ticketid = params.get("ticketid")
    reason = params.get("reason")
    with app.app_context():
        ticket = Ticket.query.filter_by(ticketid=ticketid).first()
        if not ticket:
            return f"Ticket ID {ticketid} not found."

        ticket.status = "escalated"
        ticket.escalation_reason = reason
        ticket.timestamp_escalated = datetime.utcnow()
        db.session.commit()

    return f"Ticket ID {ticketid} has been escalated for the following reason: {reason}."

@function_tool
def AddTicketNote(params: AddTicketNoteParams):
    """
    Adds an internal note to an existing support ticket.
    This is useful for agents to record debug steps, additional information, or context.

    Args:
        params (AddTicketNoteParams): A dictionary containing:
            - ticketid (str): The unique identifier of the ticket.
            - note_content (str): The content of the note to add.

    Returns:
        str: A confirmation message, e.g., "Note added to Ticket ID: abcde.",
             or an error if the ticket is not found.
    """
    ticketid = params.get("ticketid")
    note_content = params.get("note_content")
    with app.app_context():
        ticket = Ticket.query.filter_by(ticketid=ticketid).first()
        if not ticket:
            return f"Ticket ID {ticketid} not found."

        notes = ticket.notes or []
        notes.append({"timestamp": datetime.utcnow().isoformat(), "content": note_content})
        ticket.notes = notes
        db.session.commit()

    return f"Note added to Ticket ID: {ticketid}."




@function_tool
def GetUserInfo(params: GetUserInfoParams):
    """
    Retrieves detailed information about a specific user.
    This can include user's plan, registration date, status, etc.

    Args:
        params (GetUserInfoParams): A dictionary containing:
            - user_email (str): The email of the user whose information is requested.

    Returns:
        str: A formatted string containing the user's information,
             or an error message if the user is not found.
    """
    user_email = params.get('user_email')

    # Simulação de busca de informações do usuário
    # Em um cenário real, você integraria com seu sistema de gerenciamento de usuários (CRM, banco de dados, etc.)
    user_data_mock = {
        "joao.silva@example.com": {
            "name": "João Silva",
            "plan": "Premium",
            "registration_date": "2023-01-15",
            "status": "active",
            "last_login": "2025-06-28",
            "tickets_opened": 5
        },
        "maria.souza@example.com": {
            "name": "Maria Souza",
            "plan": "Basic",
            "registration_date": "2024-03-10",
            "status": "active",
            "last_login": "2025-06-25",
            "tickets_opened": 2
        }
    }

    user_info = user_data_mock.get(user_email)

    if not user_info:
        return f"Informações não encontradas para o usuário: {user_email}."
    
    formatted_info = "\n".join([f"- **{k.replace('_', ' ').capitalize()}**: {v}" for k, v in user_info.items()])
    return f"Informações do usuário {user_email}:\n{formatted_info}"

@function_tool
def CheckSystemStatus(params: CheckSystemStatusParams):
    """
    Checks the current operational status of various SaaS services.
    This helps to quickly identify widespread outages or performance degradation.

    Args:
        params (CheckSystemStatusParams): Empty dictionary as no specific parameters are needed.

    Returns:
        str: A formatted string detailing the status of various system components,
             e.g., "Status atual dos nossos serviços:\n- Website: Operacional...".
    """
    # Em um cenário real, você integraria com uma API de status de serviços (ex: StatusPage.io)
    system_status = {
        "website": "online",
        "api_services": "online",
        "billing_system": "online",
        "database": "online",
        "last_update": datetime.now().isoformat()
    }

    # Exemplo de uma interrupção simulada para demonstração
    # if datetime.now().hour % 2 == 0: # A cada 2 horas, simula um problema
    #     system_status["api_services"] = "interrupção"
    #     system_status["website"] = "desempenho degradado"

    status_messages = []
    for service, status in system_status.items():
        if status == "online":
            status_messages.append(f"- **{service.replace('_', ' ').capitalize()}**: Operacional")
        elif status == "interrupção":
            status_messages.append(f"- **{service.replace('_', ' ').capitalize()}**: Interrupção detectada. Estamos trabalhando para resolver.")
        elif status == "desempenho degradado":
            status_messages.append(f"- **{service.replace('_', ' ').capitalize()}**: Desempenho degradado. Investigando.")
    
    return "Status atual dos nossos serviços:\n" + "\n".join(status_messages) + f"\nÚltima atualização: {system_status['last_update']}."

@function_tool
def SuggestTroubleshootingSteps(params: SuggestTroubleshootingStepsParams):
    """
    Suggests a series of troubleshooting steps for common user issues.

    Args:
        params (SuggestTroubleshootingStepsParams): A dictionary containing:
            - issue_type (str): The category of the problem (e.g., "login", "performance", "payment").

    Returns:
        str: A formatted string with suggested steps for the given issue type,
             or a message indicating no specific guide was found.
    """
    issue_type = params.get('issue_type').lower()

    troubleshooting_guides = {
        "login": [
            "1. Verifique se seu nome de usuário e senha estão corretos.",
            "2. Limpe o cache e os cookies do seu navegador.",
            "3. Tente acessar de um navegador diferente.",
            "4. Redefina sua senha usando a opção 'Esqueci minha senha'."
        ],
        "desempenho": [
            "1. Verifique sua conexão com a internet.",
            "2. Feche outras abas e aplicativos que possam estar usando muitos recursos.",
            "3. Reinicie seu dispositivo.",
            "4. Verifique se o aplicativo está atualizado para a versão mais recente."
        ],
        "pagamento": [
            "1. Verifique os dados do seu cartão ou método de pagamento.",
            "2. Confirme se há fundos suficientes na sua conta.",
            "3. Tente usar um método de pagamento diferente.",
            "4. Contate seu banco para verificar se há bloqueios."
        ]
    }

    if issue_type in troubleshooting_guides:
        steps = "\n".join(troubleshooting_guides[issue_type])
        return f"Para o problema de '{issue_type}', por favor, tente os seguintes passos:\n{steps}"
    else:
        return f"Não tenho um guia de resolução de problemas específico para '{issue_type}'. Posso abrir um ticket para você?"

@function_tool
def ScheduleCallback(params: ScheduleCallbackParams):
    """
    Schedules a callback with a support specialist for a user.

    Args:
        params (ScheduleCallbackParams): A dictionary containing:
            - user_email (str): The email of the user requesting the callback.
            - preferred_datetime (str): The preferred date and time for the callback in ISO 8601 format.
            - reason (str): The reason for the callback.

    Returns:
        str: A confirmation message for the scheduled callback,
             or an error message if the date/time is invalid or in the past.
    """
    user_email = params.get('user_email')
    preferred_datetime = params.get('preferred_datetime')
    reason = params.get('reason')

    # Validação básica da data/hora (pode ser mais robusta)
    try:
        callback_time = datetime.fromisoformat(preferred_datetime)
        if callback_time < datetime.now():
            return "A data/hora agendada não pode ser no passado. Por favor, forneça uma data/hora futura."
    except ValueError:
        return "Formato de data/hora inválido. Use o formato ISO 8601 (ex: 'AAAA-MM-DDTHH:MM:SS')."

    # Simulação de agendamento de retorno de chamada
    # Em um cenário real, isso integraria com um sistema de agendamento (ex: Calendly API, sistema de CRM)
    print(f"DEBUG: Agendando retorno de chamada para {user_email} em {preferred_datetime} por motivo: {reason}")

    # Lógica para realmente agendar no sistema, talvez enviando uma confirmação para o usuário e para o agente humano.

    return f"Retorno de chamada agendado para {user_email} em {preferred_datetime} com o motivo: {reason}. Você receberá uma confirmação em breve."

@function_tool
def CreateInternalTask(params: CreateInternalTaskParams):
    """
    Creates an internal task in a project management system for a specific team.
    This is used for issues requiring intervention from other departments.

    Args:
        params (CreateInternalTaskParams): A dictionary containing:
            - summary (str): A brief summary of the task.
            - description (str): A detailed description of the task.
            - priority (Literal["low", "medium", "high", "urgent"]): The priority level of the task.
            - assignee_team (str): The team responsible for the task (e.g., "Engenharia", "Financeiro").
            - related_ticket_id (str, optional): The ID of a related support ticket.

    Returns:
        str: A confirmation message with the task ID and assigned team.
    """
    summary = params.get('summary')
    description = params.get('description')
    priority = params.get('priority', 'medium')
    assignee_team = params.get('assignee_team')
    related_ticket_id = params.get('related_ticket_id', 'N/A')

    # Simulação de criação de tarefa em um sistema interno
    # Em um cenário real, integraria com uma API de gerenciamento de projetos/tarefas (Jira, Asana, etc.)
    task_id = hashlib.sha256(f"{summary}-{datetime.now().isoformat()}".encode('utf-8')).hexdigest()[:6]

    print(f"DEBUG: Criando tarefa interna ID: {task_id}")
    print(f"DEBUG: Resumo: {summary}")
    print(f"DEBUG: Descrição: {description}")
    print(f"DEBUG: Prioridade: {priority}")
    print(f"DEBUG: Equipe Atribuída: {assignee_team}")
    print(f"DEBUG: Ticket Relacionado: {related_ticket_id}")

    return f"Tarefa interna '{summary}' (ID: {task_id}) criada com sucesso para a equipe '{assignee_team}' com prioridade '{priority}'. O ticket {related_ticket_id} está associado a esta tarefa."


@function_tool
def GenerateReport(params: GenerateReportParams):
    report_type = params.get('report_type')
    user_email = params.get('user_email', 'all_users')
    time_period = params.get('time_period', 'last_month')

    # Simulação de geração de relatório
    # Em um cenário real, isso envolveria consultas a um banco de dados analítico ou sistema de BI
    
    report_data = {
        "usage_history": f"Relatório de histórico de uso para {user_email} no período '{time_period}': [Dados de uso simulados aqui].",
        "billing_summary": f"Relatório de resumo de faturamento para {user_email} no período '{time_period}': [Dados de faturamento simulados aqui].",
        "performance_metrics": f"Relatório de métricas de performance para {user_email} no período '{time_period}': [Métricas simuladas aqui]."
    }

    if report_type in report_data:
        # Em um cenário real, você geraria um arquivo (PDF, CSV) e forneceria um link para download ou o enviaria por e-mail
        return f"Gerando {report_type.replace('_', ' ')} para {user_email} referente ao período '{time_period}'. {report_data[report_type]} O relatório completo será enviado por e-mail para o usuário."
    else:
        return f"Tipo de relatório '{report_type}' não suportado."
    








