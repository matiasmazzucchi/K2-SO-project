"""Módulo de configuración del bot K2-SO."""
from .settings import get_settings, Settings, AUTHORIZED_USER_NAMES, SHEET_NAMES
from .prompts import (
    get_k2_system_prompt,
    get_financial_agent_prompt,
    get_calendar_agent_prompt,
    get_nutrition_agent_prompt,
    get_shopping_agent_prompt,
    get_email_agent_prompt,
    AGENT_PROMPTS
)

__all__ = [
    "get_settings",
    "Settings",
    "AUTHORIZED_USER_NAMES",
    "SHEET_NAMES",
    "get_k2_system_prompt",
    "get_financial_agent_prompt",
    "get_calendar_agent_prompt",
    "get_nutrition_agent_prompt",
    "get_shopping_agent_prompt",
    "get_email_agent_prompt",
    "AGENT_PROMPTS"
]