"""
Agente de correo electrónico para lectura de emails.
Maneja las operaciones con Gmail API.
"""
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool

from ..config import get_settings, get_email_agent_prompt
from ..tools.gmail_tool import GmailClient


class EmailAgent:
    """
    Agente especializado en gestión de correos electrónicos.

    Maneja lectura de emails, búsqueda y consultas
    en Gmail de forma segura (solo lectura).
    """

    def __init__(self, project_id: str):
        """
        Inicializa el agente de correo.

        Args:
            project_id: ID del proyecto de Google Cloud
        """
        self.settings = get_settings()
        self.project_id = project_id
        self.gmail_client = GmailClient(project_id)

    def is_ready(self) -> bool:
        """Verifica si el agente está listo para operar."""
        return self.gmail_client.is_authenticated()

    async def get_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los emails sin leer.

        Args:
            max_results: Cantidad máxima de emails a retornar

        Returns:
            Lista de emails sin leer
        """
        return await self.gmail_client.get_unread_emails(max_results=max_results)

    async def search_emails(
        self,
        search_query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca emails según términos específicos.

        Args:
            search_query: Términos de búsqueda
            max_results: Cantidad máxima de resultados

        Returns:
            Lista de emails que coinciden con la búsqueda
        """
        return await self.gmail_client.search_emails(
            search_query=search_query,
            max_results=max_results
        )

    async def get_emails_from_sender(
        self,
        sender_email: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene emails de un remitente específico.

        Args:
            sender_email: Email del remitente
            max_results: Cantidad máxima de emails

        Returns:
            Lista de emails del remitente
        """
        return await self.gmail_client.get_emails_from_sender(
            sender_email=sender_email,
            max_results=max_results
        )

    async def get_email_details(self, message_id: str) -> Dict[str, Any]:
        """
        Obtiene los detalles completos de un email específico.

        Args:
            message_id: ID del mensaje

        Returns:
            Diccionario con detalles completos del email
        """
        return await self.gmail_client.get_email(message_id=message_id)


def create_email_tools(agent: EmailAgent) -> List:
    """
    Crea las herramientas de LangChain para el agente de correo.

    Args:
        agent: Instancia del agente de correo

    Returns:
        Lista de herramientas
    """

    @tool
    async def obtener_emails_sin_leer(limite: int = 10) -> str:
        """
        Obtiene los emails sin leer de tu bandeja de entrada.
        Úsalo cuando el usuario quiera ver sus emails no leídos.

        Args:
            limite: Cantidad máxima de emails a mostrar (por defecto 10)

        Returns:
            Lista formateada de emails sin leer
        """
        emails = await agent.get_unread_emails(max_results=limite)

        if not emails:
            return "No tienes emails sin leer. ¡Bandeja limpia!"

        result = f"📬 Tienes {len(emails)} emails sin leer:\n\n"
        for email in emails:
            result += f"📧 De: {email['from']}\n"
            result += f"   Asunto: {email['subject']}\n"
            result += f"   Fecha: {email['date']}\n"
            result += f"   Vista previa: {email['snippet'][:100]}...\n\n"

        return result

    @tool
    async def buscar_emails(terminos: str, limite: int = 10) -> str:
        """
        Busca emails según términos específicos.
        Úsalo cuando el usuario quiera buscar emails por palabra clave, remitente, etc.

        Args:
            terminos: Términos de búsqueda (ej: "cliente", "from:usuario@email.com")
            limite: Cantidad máxima de resultados (por defecto 10)

        Returns:
            Lista formateada de emails encontrados
        """
        emails = await agent.search_emails(search_query=terminos, max_results=limite)

        if not emails:
            return f"No encontré emails con los términos: {terminos}"

        result = f"🔍 Encontré {len(emails)} email(s) para: {terminos}\n\n"
        for email in emails:
            result += f"📧 De: {email['from']}\n"
            result += f"   Asunto: {email['subject']}\n"
            result += f"   Fecha: {email['date']}\n"
            result += f"   Vista previa: {email['snippet'][:100]}...\n\n"

        return result

    @tool
    async def obtener_emails_de_contacto(email_contacto: str, limite: int = 10) -> str:
        """
        Obtiene todos los emails de un contacto específico.
        Úsalo cuando el usuario quiera ver conversación con una persona específica.

        Args:
            email_contacto: Dirección de email del contacto
            limite: Cantidad máxima de emails (por defecto 10)

        Returns:
            Lista formateada de emails del contacto
        """
        emails = await agent.get_emails_from_sender(
            sender_email=email_contacto,
            max_results=limite
        )

        if not emails:
            return f"No encontré emails de: {email_contacto}"

        result = f"📨 Encontré {len(emails)} email(s) de: {email_contacto}\n\n"
        for email in emails:
            result += f"📧 Asunto: {email['subject']}\n"
            result += f"   Fecha: {email['date']}\n"
            result += f"   Vista previa: {email['snippet'][:100]}...\n\n"

        return result

    return [obtener_emails_sin_leer, buscar_emails, obtener_emails_de_contacto]
