"""
Vision Analyzer para procesamiento de imágenes.
Utiliza OpenAI GPT-4o Vision.
"""
from typing import Dict, Any, Optional
import base64
import httpx

from ..config import get_settings


class VisionAnalyzer:
    """
    Analizador de imágenes usando OpenAI Vision.
    """

    def __init__(self):
        """Inicializa el analizador de visión."""
        self.settings = get_settings()

    def is_available(self) -> bool:
        """Verifica si el servicio de visión está disponible."""
        return bool(self.settings.openai_api_key)

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza una imagen usando OpenAI GPT-4o Vision.

        Args:
            image_data: Bytes de la imagen
            prompt: Prompt personalizado

        Returns:
            Diccionario con el análisis
        """
        if not self.is_available():
            return {"error": "Vision service not available"}

        # Codificar imagen en base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Llamar a OpenAI Vision API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4-vision-preview",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt or "Analiza esta imagen en detalle"
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 1024
                    },
                    timeout=60.0
                )

                if response.status_code == 200:
                    result = response.json()
                    analysis = result['choices'][0]['message']['content']
                    return {
                        "description": analysis,
                        "food_items": [],
                        "calories": None,
                        "nutritional_info": {}
                    }
                else:
                    return {"error": f"Vision API error: {response.status_code}"}

            except Exception as e:
                return {"error": str(e)}
