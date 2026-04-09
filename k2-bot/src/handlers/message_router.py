"""
Router de mensajes para el bot K2-SO.
Enruta mensajes según su tipo (texto, audio, imagen, PDF).
"""
from typing import Optional
import asyncio

from ..config import get_settings, AUTHORIZED_USER_NAMES
from ..memory import memory_manager
from ..agents.orchestrator import K2Orchestrator
from ..utils.multimodal import multimodal_service


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
                text=message_data.get("text", ""),
                orchestrator=orchestrator,
                memory=memory,
                user_name=user_name
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
        # 1. Obtener historial previo (sin el mensaje actual)
        chat_history = memory.get_messages()

        # 2. Añadir mensaje actual a la memoria persistente
        memory.add_message("user", text)

        # 3. Procesar con el agente (pasando el historial histórico)
        response = await orchestrator.process_message(
            user_input=text,
            chat_history=chat_history,
            context={"user_name": user_name}
        )

        # 4. Guardar respuesta en memoria y persistir
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
        """
        from .telegram import telegram_handler
        
        voice_data = message_data.get("voice", {})
        file_id = voice_data.get("file_id")
        
        if not file_id:
            return "No pude obtener el archivo de voz."
            
        try:
            # 1. Descargar audio
            audio_bytes = await telegram_handler.download_file(file_id)
            
            # 2. Transcribir con Whisper
            transcribed_text = await multimodal_service.transcribe_voice(audio_bytes)
            
            if not transcribed_text:
                return "No pude entender lo que dijiste en el audio, Matz. ¿Podrías repetirlo?"
            
            # 3. Procesar como texto con el contexto de audio
            chat_history = memory.get_messages()
            memory.add_message("user", f"[Audio]: {transcribed_text}")
            
            response = await orchestrator.process_message(
                user_input=transcribed_text,
                chat_history=chat_history,
                context={"user_name": user_name, "transcribed_text": transcribed_text}
            )
            
            memory.add_message("assistant", response)
            memory.save()
            
            return response
            
        except Exception as e:
            return f"Tuve un error procesando tu audio: {str(e)}"

    async def _process_photo(
        self,
        message_data: dict,
        orchestrator: K2Orchestrator,
        memory,
        user_name: str
    ) -> str:
        """
        Procesa una imagen.
        """
        from .telegram import telegram_handler
        
        # Telegram manda un array de fotos de distintos tamaños, la última es la más grande
        photos = message_data.get("photo", [])
        if not photos:
            return "No recibí ninguna foto."
            
        file_id = photos[-1].get("file_id")
        caption = message_data.get("caption", "Analiza esta imagen.")
        
        try:
            # 1. Descargar foto
            image_bytes = await telegram_handler.download_file(file_id)
            
            # 2. Analizar con GPT-4o Vision
            image_description = await multimodal_service.analyze_image(image_bytes, prompt=caption)
            
            # 3. Procesar con el orquestador
            chat_history = memory.get_messages()
            memory.add_message("user", f"[Foto]: {caption}")
            
            response = await orchestrator.process_message(
                user_input=caption,
                chat_history=chat_history,
                context={"user_name": user_name, "image_description": image_description}
            )
            
            memory.add_message("assistant", response)
            memory.save()
            
            return response
            
        except Exception as e:
            return f"Hubo un fallo en mis sensores ópticos al procesar la imagen: {str(e)}"

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