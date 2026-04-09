"""
Utilidades para procesamiento multimodal (Voz y Visión).
"""
import io
import os
from typing import Optional
from openai import AsyncOpenAI
from ..config import get_settings

class MultimodalService:
    """
    Servicio para manejar integraciones con Whisper y GPT-4o Vision.
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def transcribe_voice(self, audio_bytes: bytes, filename: str = "voice.ogg") -> str:
        """
        Transcribe audio usando OpenAI Whisper.

        Args:
            audio_bytes: Contenido del audio
            filename: Nombre del archivo con extensión correcta

        Returns:
            Texto transcrito
        """
        # Crear un objeto tipo archivo en memoria
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        try:
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text
        except Exception as e:
            print(f"Error en transcripción Whisper: {e}")
            return ""

    async def analyze_image(self, image_bytes: bytes, prompt: str = "Describe esta imagen detalladamente.") -> str:
        """
        Analiza una imagen usando GPT-4o Vision.

        Args:
            image_bytes: Contenido de la imagen
            prompt: Instrucción para el análisis

        Returns:
            Descripción de la imagen
        """
        import base64

        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error en análisis de visión: {e}")
            return "No pude analizar la imagen correctamente."

# Instancia global
multimodal_service = MultimodalService()
