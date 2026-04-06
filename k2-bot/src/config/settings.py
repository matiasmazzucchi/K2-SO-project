"""
Configuración centralizada del bot K2-SO.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    """Configuración del proyecto cargada desde variables de entorno."""

    # Google Cloud
    project_id: str = "k2-proyect-491716"
    region: str = "us-central1"

    # Telegram
    telegram_bot_token: str = ""

    # APIs de LLM
    deepseek_api_key: str = ""
    openai_api_key: str = ""

    # OAuth Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""

    # Configuración del Bot
    bot_name: str = "K2"
    bot_personality: str = "droide imperial"
    default_timezone: str = "America/Argentina/Buenos_Aires"

    # Usuarios autorizados (IDs de Telegram)
    authorized_users: List[int] = [8071121316]

    # Memoria
    memory_window_size: int = 10
    firestore_collection: str = "conversations"

    # Google Sheets IDs
    sheets_ecosistema_mazzucchi: str = "1A5s-Rg3Y9fWOJI_tre9nciyt7wFi_y8h7Iwj3vnSIac"
    sheets_ecosistema_tachi: str = "1zKW4oyLq6SZnRjbeR1PPIKI_Y7h9lybOjxYZPyAaMLA"
    sheets_flujo_dinero: str = "1u_C69ArQ8c_OCuur_dx3wuOXPnghP6Mny8sRPnymflU"

    # Calendario
    calendar_id: str = "matiasmazzucchi1@gmail.com"

    # Gmail Configuration
    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.json"

    # Google Cloud Service Account
    google_application_credentials: str = "path/to/service-account-key.json"

    # Cloud Run
    port: int = 8080
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Retorna la instancia de configuración (singleton)."""
    return Settings()


# Constantes del sistema
AUTHORIZED_USER_NAMES = {
    8071121316: "Matz"
}

# Nombres de hojas de Google Sheets
SHEET_NAMES = {
    "egresos_variables": 1659801060,
    "validacion_egresos": 1850933724,
    "flujo_2025": 1939459563,
    "comparacion_precios": 1370180974,
    "categorias_supermercados": 1720497076
}