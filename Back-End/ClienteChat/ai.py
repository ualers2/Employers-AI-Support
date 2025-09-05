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

from modules.upload_ import upload_
from modules.download_ import download_


# Configuração de logging
logger = logging.getLogger(__name__)

class ConversationType(str, Enum):
    SUPPORT = "support"
    MARKETING = "marketing"
    GENERAL = "general"
    ONBOARDING = "onboarding"

class UserIntent(str, Enum):
    QUESTION = "question"
    COMPLAINT = "complaint"
    FEATURE_REQUEST = "feature_request"
    PRICING_INFO = "pricing_info"
    DEMO_REQUEST = "demo_request"
    TECHNICAL_HELP = "technical_help"
    ACCOUNT_ISSUE = "account_issue"

class ResponseTone(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    EMPATHETIC = "empathetic"
    ENTHUSIASTIC = "enthusiastic"

class AI_CustomerChatOutput(BaseModel):
    content: str = Field(..., description="A resposta principal para o usuário")
    conversation_type: ConversationType = Field(..., description="Tipo de conversa identificado")
    user_intent: UserIntent = Field(..., description="Intenção do usuário identificada")
    response_tone: ResponseTone = Field(..., description="Tom de voz usado na resposta")
    next_steps: Optional[List[str]] = Field(None, description="Próximos passos sugeridos")
    escalation_needed: bool = Field(False, description="Se precisa escalar para humano")
    follow_up_suggestions: Optional[List[str]] = Field(None, description="Sugestões de follow-up")

class CustomerChatAnalytics(BaseModel):
    user_satisfaction_score: int = Field(..., ge=1, le=5, description="Score de satisfação estimado (1-5)")
    conversation_summary: str = Field(..., description="Resumo da conversa")
    key_topics: List[str] = Field(..., description="Tópicos principais abordados")
    marketing_opportunities: Optional[List[str]] = Field(None, description="Oportunidades de marketing identificadas")

async def CustomerChatAgent(
    content_user: str,
    UPLOAD_FOLDER: str,
    user_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-4o-mini",
    UPLOAD_URL: str = os.getenv("UPLOAD_URL"),
    USER_ID: str = "default_user",
    enable_analytics: bool = True
):
    """
    Agente de Chat do Cliente refinado para suporte e marketing
    
    Args:
        content_user: Mensagem do usuário
        user_context: Contexto do usuário (plano, empresa, histórico, etc.)
        conversation_history: Histórico da conversa atual
        model: Modelo de IA a ser usado
        enable_analytics: Se deve gerar analytics da conversa
    """
    
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
    # os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Download e processamento dos documentos
    contents = await _load_company_documents(
        company_documents, filenames, UPLOAD_FOLDER, UPLOAD_URL, USER_ID
    )
    
    # Análise do contexto do usuário
    user_profile = _analyze_user_context(user_context)
    
    # Histórico da conversa formatado
    formatted_history = _format_conversation_history(conversation_history)
    
    # Prompt system refinado
    prompt_system = _build_system_prompt(contents, user_profile, formatted_history)
    
    # Configuração do agente
    agent = Agent(
        name="Customer Chat Assistant",
        instructions=prompt_system,
        model=model,
        output_type=AI_CustomerChatOutput,
    )
    
    # Execução do agente
    try:
        result = await Runner.run(
            agent, 
            content_user, 
            max_turns=300,
        )
        response = result.final_output
        
        # Analytics opcionais
        analytics = None
        if enable_analytics:
            analytics = await _generate_analytics(content_user, response, conversation_history)
        
        # Log da interação
        logger.info(f"Chat interaction completed - User: {USER_ID}, Type: {response.conversation_type}")
        
        return {
            "response": response,
            "analytics": analytics,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Erro no CustomerChatAgent: {str(e)}")
        return {
            "response": _fallback_response(content_user),
            "analytics": None,
            "success": False,
            "error": str(e)
        }

async def _load_company_documents(company_docs: Dict, filenames: List[str], 
                                upload_folder: str, upload_url: str, user_id: str) -> str:
    """Carrega e processa documentos da empresa"""
    contents = []
    
    for filename, file_id in zip(filenames, company_docs.values()):
        try:
            storage_rel_path = os.path.join(
                upload_folder, 
                "files",
                datetime.utcnow().strftime("%Y/%m/%d"),
            )
            os.makedirs(storage_rel_path, exist_ok=True)

            storage_abs_path = os.path.join(storage_rel_path, filename)
            
            if os.path.exists(storage_abs_path):
                path_file = storage_abs_path
            else:
                path_file = download_(upload_url, storage_abs_path, "support", file_id, "freitasalexandre810@gmail_com")

            with open(path_file, "r", encoding="utf-8") as f:
                content = f.read()
                contents.append(f"### {filename}\n{content}")
                
        except Exception as e:
            logger.warning(f"Erro ao carregar {filename}: {str(e)}")
            contents.append(f"### {filename}\n[Documento não disponível]")
    
    return "\n\n".join(contents)

def _analyze_user_context(user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa contexto do usuário para personalização"""
    if not user_context:
        return {"type": "new_visitor", "priority": "normal"}
    
    profile = {
        "type": user_context.get("user_type", "unknown"),
        "plan": user_context.get("current_plan", "free"),
        "company_size": user_context.get("company_size", "unknown"),
        "industry": user_context.get("industry", "unknown"),
        "priority": "normal"
    }
    
    # Define prioridade baseada no contexto
    if profile["plan"] in ["enterprise", "pro"]:
        profile["priority"] = "high"
    elif profile["type"] == "trial_user":
        profile["priority"] = "medium"
        
    return profile

def _format_conversation_history(history: Optional[List[Dict[str, str]]]) -> str:
    """Formata histórico da conversa"""
    if not history:
        return "Primeira interação do usuário."
    
    formatted = []
    for msg in history[-5:]:  # Últimas 5 mensagens
        role = msg.get("role", "user")
        content = msg.get("content", "")
        formatted.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(formatted)

def _build_system_prompt(contents: str, user_profile: Dict, history: str) -> str:
    """Constrói o prompt system personalizado"""
    
    return f"""
    Você é o assistente inteligente de atendimento ao cliente do aplicativo Media Cuts Studio. Sua função é:

    ## PERFIL DO USUÁRIO
    - Tipo: {user_profile.get('type', 'desconhecido')}
    - Plano: {user_profile.get('plan', 'free')}
    - Prioridade: {user_profile.get('priority', 'normal')}
    - Empresa: {user_profile.get('company_size', 'não informado')}
    - Setor: {user_profile.get('industry', 'não informado')}

    ## HISTÓRICO DA CONVERSA
    {history}

    ## DOCUMENTAÇÃO DA EMPRESA
    {contents}

    ## INSTRUÇÕES PRINCIPAIS
    - Nunca responda com textos longos e cançativo, principalmente por estamos lidando com publico brasileiro que por sua definicao nao le 2 livro por ano. 

    ### COMO ASSISTENTE DE SUPORTE:
    1. **Resolução Proativa**: Antecipe necessidades e ofereça soluções completas

    ## REGRAS DE COMPORTAMENTO

    ### TOM E PERSONALIDADE:
    - **Profissional mas humano**: Seja competente sem ser robótico
    - **Proativo**: Antecipe necessidades e ofereça valor adicional
    - **Empático**: Reconheça frustrações e demonstre compreensão
    - **Consultivo**: Atue como consultor, não apenas respondedor

    ### ESTRUTURA DE RESPOSTA:
    1. **Reconhecimento**: Confirme que entendeu a situação
    2. **Solução Principal**: Resposta direta e clara
    3. **Valor Adicional**: Informações extras relevantes
    4. **Próximos Passos**: Ações concretas sugeridas

    ### IDENTIFICAÇÃO DE CONTEXTO:
    - **Suporte**: Problemas técnicos, bugs, dúvidas de uso, account issues
    - **Marketing**: Interesse em features, comparações, pricing, demos
    - **Onboarding**: Novos usuários, primeiros passos, configurações
    - **Geral**: Dúvidas sobre empresa, políticas, informações gerais

    ## OUTPUT REQUIRED:
    - Sempre identifique: conversation_type, user_intent, response_tone
    - Sugira next_steps específicos e acionáveis
    - Marque escalation_needed quando apropriado
    - Ofereça follow_up_suggestions relevantes

    Responda sempre de forma útil, precisa e orientada a resultados. Sua missão é resolver problemas E identificar oportunidades de crescimento para o usuário e para a empresa.
    """

def _fallback_response(user_message: str) -> AI_CustomerChatOutput:
    """Resposta de fallback em caso de erro"""
    return AI_CustomerChatOutput(
        content=f"Obrigado por entrar em contato! Estou processando sua mensagem: '{user_message[:100]}...' "
               f"Nosso time irá retornar em breve com uma resposta completa. "
               f"Para urgências, você pode contatar nosso suporte direto.",
        conversation_type=ConversationType.GENERAL,
        user_intent=UserIntent.QUESTION,
        response_tone=ResponseTone.PROFESSIONAL,
        escalation_needed=True,
        next_steps=["Aguardar resposta do suporte", "Verificar documentação disponível"]
    )

async def _generate_analytics(user_message: str, response: AI_CustomerChatOutput, 
                            history: Optional[List[Dict]]) -> CustomerChatAnalytics:
    """Gera analytics da conversa"""
    
    # Analytics básicos (pode ser expandido com ML)
    satisfaction_score = 4  # Default otimista
    
    if response.escalation_needed:
        satisfaction_score = 3
    elif response.conversation_type == ConversationType.SUPPORT and "problema" in user_message.lower():
        satisfaction_score = 3
    elif response.conversation_type == ConversationType.MARKETING:
        satisfaction_score = 5
    
    topics = []
    marketing_ops = []
    
    # Análise simples de tópicos
    if "preço" in user_message.lower() or "pricing" in user_message.lower():
        topics.append("pricing")
        marketing_ops.append("Interesse em pricing - oportunidade de demo")
    
    if "feature" in user_message.lower() or "funcionalidade" in user_message.lower():
        topics.append("features")
        marketing_ops.append("Interesse em features - oportunidade de upgrade")
    
    if not topics:
        topics = ["general_inquiry"]
    
    return CustomerChatAnalytics(
        user_satisfaction_score=satisfaction_score,
        conversation_summary=f"Usuário {response.user_intent.value} sobre {response.conversation_type.value}",
        key_topics=topics,
        marketing_opportunities=marketing_ops if marketing_ops else None
    )

# Função de teste refinada
async def test_customer_chat(UPLOAD_URL, UPLOAD_FOLDER):
    """Testa diferentes cenários do chat"""
    
    test_scenarios = [
        {
            "message": "Como faço para integrar com minha API?",
            "context": {"user_type": "trial_user", "current_plan": "free"},
            "expected_type": ConversationType.SUPPORT
        },
        {
            "message": "Quais são os preços dos planos pagos?",
            "context": {"user_type": "prospect", "company_size": "50-200"},
            "expected_type": ConversationType.MARKETING
        },
        {
            "message": "Acabei de criar minha conta, por onde começar?",
            "context": {"user_type": "new_user", "current_plan": "free"},
            "expected_type": ConversationType.ONBOARDING
        }
    ]
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n--- Teste {i+1}: {scenario['expected_type']} ---")
        result = await CustomerChatAgent(
            content_user=scenario["message"],
            user_context=scenario["context"],
            UPLOAD_URL=UPLOAD_URL,
            UPLOAD_FOLDER=UPLOAD_FOLDER
        )
        
        if result["success"]:
            response = result["response"]
            print(f"Resposta: {response.content}...")
            print(f"Tipo identificado: {response.conversation_type}")
            print(f"Intenção: {response.user_intent}")
            print(f"Próximos passos: {response.next_steps}")
        else:
            print(f"Erro: {result['error']}")

# if __name__ == "__main__":
#     asyncio.run(test_customer_chat())
