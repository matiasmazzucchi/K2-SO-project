"""
Orquestador principal del agente K2-SO.
Coordina los sub-agentes y gestiona el flujo de conversación.
"""
from typing import Optional, Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_deepseek import ChatDeepSeek

from ..config import get_settings, get_k2_system_prompt, AUTHORIZED_USER_NAMES
from ..memory import FirestoreConversationMemory
from .financial import FinancialAgent, create_financial_tools
from .calendar import CalendarAgent, create_calendar_tools
from .nutrition import NutritionAgent, create_nutrition_tools
from .email import EmailAgent, create_email_tools


class K2Orchestrator:
    """
    Orquestador principal del bot K2-SO.

    Coordina los diferentes sub-agentes y gestiona
    la memoria de conversación.
    """

    def __init__(self, project_id: str, user_id: int):
        """
        Inicializa el orquestador.

        Args:
            project_id: ID del proyecto de Google Cloud
            user_id: ID de Telegram del usuario
        """
        self.settings = get_settings()
        self.project_id = project_id
        self.user_id = user_id
        self.user_name = AUTHORIZED_USER_NAMES.get(user_id, "Usuario")

        # Configurar LLM principal
        self.llm = self._configure_llm()

        # Inicializar sub-agentes
        self.financial_agent = FinancialAgent(project_id)
        self.calendar_agent = CalendarAgent(project_id)
        self.nutrition_agent = NutritionAgent()
        self.email_agent = EmailAgent(project_id)

        # Crear agente con herramientas
        self.agent_executor = self._create_agent_executor()

    def _configure_llm(self) -> ChatDeepSeek:
        """Configura el modelo de lenguaje principal."""
        return ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.7,
            api_key=self.settings.deepseek_api_key
        )

    def _create_agent_executor(self) -> AgentExecutor:
        """
        Crea el ejecutor del agente con todas las herramientas.

        Returns:
            AgentExecutor configurado
        """
        # Recopilar todas las herramientas de los sub-agentes
        tools = []
        tools.extend(create_financial_tools(self.financial_agent))
        tools.extend(create_calendar_tools(self.calendar_agent))
        tools.extend(create_nutrition_tools(self.nutrition_agent))
        tools.extend(create_email_tools(self.email_agent))

        # Crear prompt del sistema
        system_prompt = get_k2_system_prompt(self.user_name)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Crear agente
        agent = create_tool_calling_agent(self.llm, tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=self.settings.debug,
            handle_parsing_errors=True,
            max_iterations=5
        )

    async def process_message(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Procesa un mensaje del usuario y devuelve la respuesta.

        Args:
            user_input: Texto o instrucción del usuario
            context: Contexto adicional (imagen, audio transcrito, etc.)

        Returns:
            Respuesta del agente K2
        """
        context = context or {}

        # Preparar input para el agente
        input_text = user_input
        if context.get("image_description"):
            input_text = f"[Imagen: {context['image_description']}]\n{user_input}"
        elif context.get("transcribed_text"):
            input_text = f"[Audio transcrito: {context['transcribed_text']}]"

        try:
            # Ejecutar agente
            response = await self.agent_executor.ainvoke({
                "input": input_text,
                "chat_history": []  # Se maneja externamente
            })

            return response.get("output", "No pude procesar tu solicitud.")

        except Exception as e:
            print(f"Error en el agente: {e}")
            return f"Hmm, parece que tengo un problema con mis circuitos. Error: {str(e)}"

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Retorna el estado de los sub-agentes.

        Returns:
            Diccionario con el estado de cada agente
        """
        return {
            "financial": self.financial_agent.is_ready(),
            "calendar": self.calendar_agent.is_ready(),
            "nutrition": self.nutrition_agent.is_ready(),
            "email": self.email_agent.is_ready()
        }