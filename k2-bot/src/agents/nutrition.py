"""
Agente nutricional para análisis de imágenes de comida.
Utiliza GPT-4o Vision para analizar alimentos.
"""
from typing import List, Dict, Any, Optional
import base64

from langchain_core.tools import tool

from ..config import get_settings, get_nutrition_agent_prompt
from ..tools.vision_tool import VisionAnalyzer


class NutritionAgent:
    """
    Agente especializado en análisis nutricional de imágenes.

    Utiliza GPT-4o Vision para identificar alimentos,
    estimar calorías y proporcionar información nutricional.
    """

    def __init__(self):
        """Inicializa el agente nutricional."""
        self.settings = get_settings()
        self.vision_analyzer = VisionAnalyzer()

    def is_ready(self) -> bool:
        """Verifica si el agente está listo para operar."""
        return self.vision_analyzer.is_available()

    async def analyze_food_image(
        self,
        image_data: bytes,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza una imagen de comida.

        Args:
            image_data: Bytes de la imagen
            prompt: Prompt personalizado (opcional)

        Returns:
            Diccionario con el análisis nutricional
        """
        default_prompt = """Analiza y describe la imagen. Describe brevemente el entorno
        de la imagen pero describe ampliamente el objeto al que se le está haciendo foco.
        En caso de que sea un alimento observa detenidamente qué alimento es para así
        poder aproximar la cantidad de calorías que tiene. Si es un alimento describe
        qué alimento es y su información nutricional."""

        analysis = await self.vision_analyzer.analyze_image(
            image_data=image_data,
            prompt=prompt or default_prompt
        )

        return {
            "description": analysis.get("description", ""),
            "food_items": analysis.get("food_items", []),
            "estimated_calories": analysis.get("calories", None),
            "nutritional_info": analysis.get("nutritional_info", {})
        }


def create_nutrition_tools(agent: NutritionAgent) -> List:
    """
    Crea las herramientas de LangChain para el agente nutricional.

    Args:
        agent: Instancia del agente nutricional

    Returns:
        Lista de herramientas
    """

    @tool
    async def analizar_imagen_comida(descripcion_imagen: str) -> str:
        """
        Analiza una imagen de comida proporcionada por el usuario.
        Úsalo cuando el usuario envíe una foto de comida.

        Nota: La imagen se procesa automáticamente antes de llamar a esta herramienta.

        Args:
            descripcion_imagen: Descripción de la imagen ya procesada

        Returns:
            Análisis nutricional de la imagen
        """
        # Esta herramienta se usa como contexto - el análisis real
        # se hace en el router de mensajes antes de llegar al agente
        return f"Análisis nutricional: {descripcion_imagen}"

    return [analizar_imagen_comida]