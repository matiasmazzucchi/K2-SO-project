"""
Router de mensajes para el bot K2-SO.
Enruta mensajes según su tipo (texto, audio, imagen, PDF).
"""
from typing import Optional
import asyncio

from ..config import get_settings, AUTHORIZED_USER_NAMES
from ..memory import memory_manager
from ..agents.orchestrator import K2Orchestrator


class MessageRouter:
    """
    Enruta mensajes según su tipo y los procesa con el agente apropiado.
    """

    def __init__(self):
        self.settings = get_settings()
        self._orchestrators: dict = {}

    def _get_orchestrator(self, user_id: int) -> K2Orchestrator:
        """
        Obtiene o crea un orquestador para el usuario.

        Args:
            user_id: ID de Telegram del usuario

        Returns:
            Instancia de K2Orchestrator
        """
        if user_id not in self._orchestrators:
            self._orchestrators[user_id] = K2Orchestrator(
                project_id=self.settings.project_id,
                user_id=user_id
            )
        return self._orchestrators[user_id]

    async def route(
        self,
        message_type: str,
        message_data: dict,
        user_info: dict,
        auth_info: dict
    ) -> str:
        """
        Enruta un mensaje según su tipo.

        Args:
            message_type: Tipo de mensaje (text, voice, photo, pdf)
            message_data: Datos del mensaje de Telegram
            user_info: Información del usuario
            auth_info: Información de autorización

        Returns:
            Respuesta del agente
        """
        user_id = user_info["user_id"]
        user_name = AUTHORIZED_USER_NAMES.get(user_id, "Usuario")

        # Obtener orquestador y memoria
        orchestrator = self._get_orchestrator(user_id)
        memory = memory_manager.get_memory(user_id)

        # Procesar según el tipo
        if message_type == "text":
            return await self._process_text(
                message_data.get("text", ""),
                orchestrator,
                memory,
                user_name
            )
        elif message_type == "voice":
            return await self._process_voice(
                message_data,
                orchestrator,
                memory,
                user_name
            )
        elif message_type == "photo":
            return await self._process_photo(
                message_data,
                orchestrator,
                memory,
                user_name
            )
        elif message_type == "pdf":
            return await self._process_pdf(
                message_data,
                orchestrator,
                memory,
                user_name
            )
        else:
            return "No puedo procesar este tipo de mensaje. ¿Podrías enviar texto, audio, imagen o PDF?"

    async def _process_text(
        self,
        text: str,
        orchestrator: K2Orchestrator,
        memory,
        user_name: str
    ) -> str:
        """
        Procesa un mensaje de texto.

        Args:
            text: Texto del mensaje
            orchestrator: Orquestador K2
            memory: Memoria de conversación
            user_name: Nombre del usuario

        Returns:
            Respuesta del agente
        """
        # Añadir mensaje a la memoria
        memory.add_message("user", text)

        # Procesar con el agente
        response = await orchestrator.process_message(
            user_input=text,
            context={"user_name": user_name}
        )

        # Guardar respuesta en memoria
        memory.add_message("assistant", response)
        memory.save()

        return response

    async def _process_voice(
        self,
        message_data: dict,
        orchestrator: K2Orchestrator,
        memory,
        user_name: str
    ) -> str:
        """
        Procesa un mensaje de voz.

        Args:
            message_data: Datos del mensaje de Telegram
            orchestrator: Orquestador K2
            memory: Memoria de conversación
            user_name: Nombre del usuario

        Returns:
            Respuesta del agente
        """
        # TODO: Implementar transcripción con Whisper
        # Por ahora, retornar mensaje placeholder
        return "Recibí tu audio. Pronto podré transcribirlo y procesarlo."

    async def _process_photo(
        self,
        message_data: dict,
        orchestrator: K2Orchestrator,
        memory,
        user_name: str
    ) -> str:
        """
        Procesa una imagen.

        Args:
            message_data: Datos del mensaje de Telegram
            orchestrator: Orquestador K2
            memory: Memoria de conversación
            user_name: Nombre del usuario

        Returns:
            Respuesta del agente
        """
        # TODO: Implementar análisis con GPT-4o Vision
        # Por ahora, retornar mensaje placeholder
        return "Recibí tu imagen. Pronto podré analizarla."

    async def _process_pdf(
        self,
        message_data: dict,
        orchestrator: K2Orchestrator,
        memory,
        user_name: str
    ) -> str:
        """
        Procesa un documento PDF.

        Args:
            message_data: Datos del mensaje de Telegram
            orchestrator: Orquestador K2
            memory: Memoria de conversación
            user_name: Nombre del usuario

        Returns:
            Respuesta del agente
        """
        # TODO: Implementar extracción de texto de PDF
        # Por ahora, retornar mensaje placeholder
        return "Recibí tu PDF. Pronto podré extraer y analizar su contenido."