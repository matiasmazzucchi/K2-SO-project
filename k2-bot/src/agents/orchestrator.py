"""
Orquestador principal del agente K2-SO.
Coordina los sub-agentes y gestiona el flujo de conversación.
"""
from typing import Optional, Dict, Any, List
import logging

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config import get_settings, get_k2_system_prompt, AUTHORIZED_USER_NAMES
from ..memory import FirestoreConversationMemory
from .financial import FinancialAgent, create_financial_tools
from .calendar import CalendarAgent, create_calendar_tools
from .nutrition import NutritionAgent, create_nutrition_tools
from .email import EmailAgent, create_email_tools

logger = logging.getLogger(__name__)

class K2Orchestrator:
    """
    Orquestador principal del bot K2-SO.
    Usa OpenAI como cerebro principal para mayor estabilidad.
    """

    def __init__(self, project_id: str, user_id: int):
        self.settings = get_settings()
        self.project_id = project_id
        self.user_id = user_id
        self.user_name = AUTHORIZED_USER_NAMES.get(user_id, "Usuario")

        # Configurar LLM principal (Cambiado a OpenAI para estabilidad)
        self.llm = self._configure_llm()

        # Inicializar sub-agentes
        self.financial_agent = FinancialAgent(project_id)
        self.calendar_agent = CalendarAgent(project_id)
        self.nutrition_agent = NutritionAgent()
        self.email_agent = EmailAgent(project_id)

        # Crear agente con herramientas
        self.agent_executor = self._create_agent_executor()

    def _configure_llm(self) -> ChatOpenAI:
        """Configura el modelo de lenguaje principal (OpenAI)."""
        api_key = self.settings.openai_api_key.strip()
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=api_key
        )

    def _create_agent_executor(self):
        """Crea el ejecutor del agente usando LangGraph."""
        tools = []
        tools.extend(create_financial_tools(self.financial_agent))
        tools.extend(create_calendar_tools(self.calendar_agent))
        tools.extend(create_nutrition_tools(self.nutrition_agent))
        tools.extend(create_email_tools(self.email_agent))

        system_content = get_k2_system_prompt(self.user_name)
        
        try:
            from langgraph.prebuilt import create_react_agent
            agent = create_react_agent(self.llm, tools, prompt=system_content)
            return agent
        except Exception as e:
            print(f"FAILED TO CREATE AGENT: {type(e).__name__} - {e}")
            logger.error(f"Error creando agente (LangGraph): {e}")
            raise e

    async def process_message(
        self,
        user_input: str,
        chat_history: List[dict] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        context = context or {}
        chat_history = chat_history or []

        lc_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                lc_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_history.append(AIMessage(content=msg["content"]))

        input_text = user_input
        if context.get("image_description"):
            input_text = f"[Imagen: {context['image_description']}]\n{user_input}"
        elif context.get("transcribed_text"):
            input_text = f"[Audio transcrito: {context['transcribed_text']}]"

        try:
            if self.agent_executor:
                # Usando langgraph
                messages_to_send = lc_history + [HumanMessage(content=input_text)]
                response = await self.agent_executor.ainvoke({"messages": messages_to_send})
                
                final_messages = response.get("messages", [])
                if final_messages:
                    return final_messages[-1].content
                return "No pude procesar tu solicitud adecuadamente."
            else:
                # Modo fallback (sin herramientas)
                messages = [SystemMessage(content=get_k2_system_prompt(self.user_name))] + lc_history + [HumanMessage(content=input_text)]
                response = await self.llm.ainvoke(messages)
                return response.content
        except Exception as e:
            logger.error(f"Error en el agente K2: {e}")
            return f"Lo siento, Matz. Tengo un problema de conexión con mis sistemas centrales. (Error: {str(e)})"

    def get_agent_status(self) -> Dict[str, Any]:
        return {
            "financial": self.financial_agent.is_ready(),
            "calendar": self.calendar_agent.is_ready(),
            "nutrition": self.nutrition_agent.is_ready(),
            "email": self.email_agent.is_ready()
        }