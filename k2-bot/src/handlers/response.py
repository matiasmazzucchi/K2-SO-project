"""
Generador de respuestas para el bot K2-SO.
Maneja respuestas de texto y audio.
"""
import httpx
from typing import Optional
from ..config import get_settings


class ResponseGenerator:
    """
    Genera respuestas para el bot, incluyendo
    conversión a audio cuando es necesario.
    """

    def __init__(self):
        self.settings = get_settings()

    async def generate_audio_response(self, text: str) -> Optional[bytes]:
        """
        Genera una respuesta de audio usando OpenAI TTS.

        Args:
            text: Texto a convertir a audio

        Returns:
            Bytes del audio o None si hay error
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "tts-1",
                        "input": text,
                        "voice": "onyx",
                        "speed": 1.7
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.content
                else:
                    print(f"Error en TTS: {response.status_code}")
                    return None

            except Exception as e:
                print(f"Error generando audio: {e}")
                return None

    def format_response(self, response: str, format_type: str = "text") -> str:
        """
        Formatea la respuesta según el tipo.

        Args:
            response: Texto de la respuesta
            format_type: Tipo de formato (text, markdown)

        Returns:
            Respuesta formateada
        """
        if format_type == "markdown":
            # Escapar caracteres especiales de Markdown
            response = response.replace("_", "\\_")
            response = response.replace("*", "\\*")
            return response
        return response