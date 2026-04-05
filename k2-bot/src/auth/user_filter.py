"""
Módulo de autorización de usuarios.
Filtra mensajes para permitir solo usuarios autorizados.
"""
from typing import Optional
from ..config import get_settings, AUTHORIZED_USER_NAMES


class UserAuthorizationError(Exception):
    """Excepción lanzada cuando un usuario no está autorizado."""
    pass


def validate_user(user_id: int) -> bool:
    """
    Verifica si un usuario está autorizado para usar el bot.

    Args:
        user_id: ID de Telegram del usuario

    Returns:
        True si el usuario está autorizado, False en caso contrario
    """
    settings = get_settings()
    return user_id in settings.authorized_users


def get_user_name(user_id: int) -> Optional[str]:
    """
    Obtiene el nombre del usuario autorizado.

    Args:
        user_id: ID de Telegram del usuario

    Returns:
        Nombre del usuario o None si no está autorizado
    """
    return AUTHORIZED_USER_NAMES.get(user_id)


def authorize_request(telegram_user_id: int) -> dict:
    """
    Valida y autoriza una solicitud entrante.

    Args:
        telegram_user_id: ID de Telegram del usuario

    Returns:
        Diccionario con información del usuario autorizado

    Raises:
        UserAuthorizationError: Si el usuario no está autorizado
    """
    if not validate_user(telegram_user_id):
        raise UserAuthorizationError(
            f"Usuario {telegram_user_id} no autorizado"
        )

    return {
        "user_id": telegram_user_id,
        "user_name": get_user_name(telegram_user_id) or "Usuario",
        "authorized": True
    }


def extract_user_info(telegram_message: dict) -> dict:
    """
    Extrae información del usuario de un mensaje de Telegram.

    Args:
        telegram_message: Diccionario con el mensaje de Telegram

    Returns:
        Diccionario con user_id, chat_id y otra información relevante
    """
    from_user = telegram_message.get("from", {})
    chat = telegram_message.get("chat", {})

    return {
        "user_id": from_user.get("id"),
        "user_name": from_user.get("first_name", "Usuario"),
        "username": from_user.get("username"),
        "chat_id": chat.get("id"),
        "message_id": telegram_message.get("message_id"),
        "date": telegram_message.get("date")
    }