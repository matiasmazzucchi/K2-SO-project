"""Módulo de agentes especializados."""
from .orchestrator import K2Orchestrator
from .financial import FinancialAgent, create_financial_tools
from .calendar import CalendarAgent, create_calendar_tools
from .nutrition import NutritionAgent, create_nutrition_tools
from .email import EmailAgent, create_email_tools
from .shopping import ShoppingAgent, create_shopping_tools

__all__ = [
    "K2Orchestrator",
    "FinancialAgent",
    "create_financial_tools",
    "CalendarAgent",
    "create_calendar_tools",
    "NutritionAgent",
    "create_nutrition_tools",
    "EmailAgent",
    "create_email_tools",
    "ShoppingAgent",
    "create_shopping_tools"
]