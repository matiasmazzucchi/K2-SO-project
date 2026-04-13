"""
Handler de Telegram para el bot K2-SO.
Maneja webhooks y procesa mensajes entrantes.
"""
import asyncio
from typing import Optional
from fastapi import Request
import httpx

from ..config import get_settings
from ..auth import authorize_request, extract_user_info, UserAuthorizationError
from ..memory import memory_manager
from .message_router import MessageRouter
from .response import ResponseGenerator


class TelegramWebhookHandler:
    """
    Maneja webhooks de Telegram y enruta mensajes.
    """

    def __init__(self):
        self.settings = get_settings()
        self.message_router = MessageRouter()
        self.response_generator = ResponseGenerator()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP."""
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def handle_webhook(self, request: Request) -> dict:
        """
        Procesa un webhook de Telegram.

        Args:
            request: Request de FastAPI

        Returns:
            Diccionario con el resultado del procesamiento
        """
        try:
            body = await request.json()
            message = body.get("message", {})

            # Extraer información del usuario
            user_info = extract_user_info(message)
            user_id = user_info["user_id"]
            chat_id = user_info["chat_id"]

            # Autorizar usuario
            try:
                auth_info = authorize_request(user_id)
            except UserAuthorizationError:
                # Usuario no autorizado - ignorar silenciosamente
                return {"status": "unauthorized", "user_id": user_id}

            # Obtener tipo de mensaje y contenido
            message_type = self._detect_message_type(message)

            # Procesar según el tipo
            response = await self.message_router.route(
                message_type=message_type,
                message_data=message,
                user_info=user_info,
                auth_info=auth_info
            )

            # Generar y enviar respuesta
            await self._send_response(chat_id, response, message_type)

            return {"status": "success", "user_id": user_id}

        except Exception as e:
            print(f"Error procesando webhook: {e}")
            return {"status": "error", "error": str(e)}

    def _detect_message_type(self, message: dict) -> str:
        """
        Detecta el tipo de mensaje de Telegram.

        Args:
            message: Diccionario del mensaje de Telegram

        Returns:
            Tipo de mensaje: "text", "voice", "photo", "document"
        """
        if message.get("text"):
            return "text"
        elif message.get("voice"):
            return "voice"
        elif message.get("photo"):
            return "photo"
        elif message.get("document"):
            doc = message.get("document", {})
            mime_type = doc.get("mime_type", "")
            if mime_type == "application/pdf":
                return "pdf"
            return "document"
        else:
            return "unknown"

    async def _send_response(
        self,
        chat_id: int,
        response: str,
        message_type: str
    ) -> None:
        """
        Envía una respuesta a Telegram.

        Args:
            chat_id: ID del chat
            response: Texto de la respuesta
            message_type: Tipo de mensaje original
        """
        client = await self._get_client()
        token = self.settings.telegram_bot_token.strip()
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": response,
            "parse_mode": "Markdown"
        }

        try:
            await client.post(url, json=payload)
        except Exception as e:
            print(f"Error enviando respuesta a Telegram: {e}")

    async def send_audio_response(
        self,
        chat_id: int,
        audio_url: str
    ) -> None:
        """
        Envía una respuesta de audio a Telegram.

        Args:
            chat_id: ID del chat
            audio_url: URL del archivo de audio
        """
        client = await self._get_client()
        token = self.settings.telegram_bot_token.strip()
        url = f"https://api.telegram.org/bot{token}/sendAudio"

        payload = {
            "chat_id": chat_id,
            "audio": audio_url
        }

        try:
            await client.post(url, json=payload)
        except Exception as e:
            print(f"Error enviando audio a Telegram: {e}")

    async def download_file(self, file_id: str) -> bytes:
        """
        Descarga un archivo de Telegram.

        Args:
            file_id: ID del archivo en Telegram

        Returns:
            Contenido del archivo en bytes
        """
        client = await self._get_client()

        token = self.settings.telegram_bot_token.strip()
        # Obtener URL del archivo
        get_file_url = f"https://api.telegram.org/bot{token}/getFile"
        response = await client.get(get_file_url, params={"file_id": file_id})
        file_info = response.json()

        if not file_info.get("ok"):
            raise Exception(f"Error obteniendo info del archivo: {file_info}")

        file_path = file_info["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"

        # Descargar archivo
        file_response = await client.get(download_url)
        return file_response.content


# Instancia global del handler
telegram_handler = TelegramWebhookHandler()