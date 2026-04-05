"""
Agente de calendario para gestión de eventos.
Maneja las operaciones con Google Calendar.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from langchain_core.tools import tool

from ..config import get_settings, get_calendar_agent_prompt
from ..tools.calendar_tool import GoogleCalendarClient


class CalendarAgent:
    """
    Agente especializado en gestión de calendario.

    Maneja eventos, recordatorios y consultas
    de calendario en Google Calendar.
    """

    def __init__(self, project_id: str):
        """
        Inicializa el agente de calendario.

        Args:
            project_id: ID del proyecto de Google Cloud
        """
        self.settings = get_settings()
        self.project_id = project_id
        self.calendar_client = GoogleCalendarClient(project_id)
        self.default_event_duration = timedelta(minutes=30)

    def is_ready(self) -> bool:
        """Verifica si el agente está listo para operar."""
        return self.calendar_client.is_authenticated()

    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene eventos del calendario.

        Args:
            start_date: Fecha de inicio (por defecto hoy)
            end_date: Fecha de fin (por defecto +7 días)
            max_results: Máximo número de resultados

        Returns:
            Lista de eventos
        """
        tz = pytz.timezone(self.settings.default_timezone)
        now = datetime.now(tz)

        if not start_date:
            start_date = now
        if not end_date:
            end_date = now + timedelta(days=7)

        events = await self.calendar_client.get_events(
            calendar_id=self.settings.calendar_id,
            start=start_date,
            end=end_date,
            max_results=max_results
        )

        return events

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo evento en el calendario.

        Args:
            summary: Título del evento
            start_time: Fecha y hora de inicio
            description: Descripción (opcional)
            location: Ubicación (opcional)

        Returns:
            Diccionario con el evento creado
        """
        end_time = start_time + self.default_event_duration

        event = await self.calendar_client.create_event(
            calendar_id=self.settings.calendar_id,
            summary=summary,
            start=start_time,
            end=end_time,
            description=description,
            location=location
        )

        return event

    async def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza un evento existente.

        Args:
            event_id: ID del evento
            updates: Campos a actualizar

        Returns:
            Diccionario con el evento actualizado
        """
        event = await self.calendar_client.update_event(
            calendar_id=self.settings.calendar_id,
            event_id=event_id,
            updates=updates
        )

        return event

    async def delete_event(self, event_id: str) -> bool:
        """
        Elimina un evento del calendario.

        Args:
            event_id: ID del evento

        Returns:
            True si se eliminó correctamente
        """
        return await self.calendar_client.delete_event(
            calendar_id=self.settings.calendar_id,
            event_id=event_id
        )


def create_calendar_tools(agent: CalendarAgent) -> List:
    """
    Crea las herramientas de LangChain para el agente de calendario.

    Args:
        agent: Instancia del agente de calendario

    Returns:
        Lista de herramientas
    """

    @tool
    async def obtener_eventos(query: str = "") -> str:
        """
        Obtiene los próximos eventos del calendario.
        Úsalo cuando el usuario pregunte por su agenda o eventos.

        Args:
            query: Consulta opcional para filtrar eventos

        Returns:
            Lista de eventos en formato texto
        """
        events = await agent.get_events()
        if not events:
            return "No hay eventos próximos en tu calendario."

        result = "Próximos eventos:\n"
        for event in events[:5]:
            start = event.get("start", {}).get("dateTime", "N/A")
            summary = event.get("summary", "Sin título")
            result += f"- {start}: {summary}\n"
        return result

    @tool
    async def crear_evento(titulo: str, fecha: str, hora: str, descripcion: str = "") -> str:
        """
        Crea un nuevo evento en el calendario.
        Úsalo cuando el usuario quiera agendar algo.

        Args:
            titulo: Título del evento
            fecha: Fecha en formato DD/MM/YYYY
            hora: Hora en formato HH:MM
            descripcion: Descripción opcional

        Returns:
            Confirmación del evento creado
        """
        try:
            tz = pytz.timezone(agent.settings.default_timezone)
            dt = datetime.strptime(f"{fecha} {hora}", "%d/%m/%Y %H:%M")
            dt = tz.localize(dt)

            event = await agent.create_event(
                summary=titulo,
                start_time=dt,
                description=descripcion
            )

            return f"Evento creado: {titulo} el {fecha} a las {hora}"
        except Exception as e:
            return f"Error al crear evento: {str(e)}"

    @tool
    async def actualizar_evento(evento_id: str, cambios: str) -> str:
        """
        Actualiza un evento existente en el calendario.
        Úsalo cuando el usuario quiera modificar un evento.

        Args:
            evento_id: ID del evento a actualizar
            cambios: Descripción de los cambios

        Returns:
            Confirmación de la actualización
        """
        # TODO: Parsear los cambios y aplicarlos
        return f"Evento {evento_id} actualizado con los cambios: {cambios}"

    @tool
    async def eliminar_evento(evento_id: str) -> str:
        """
        Elimina un evento del calendario.
        Úsalo cuando el usuario quiera cancelar un evento.

        Args:
            evento_id: ID del evento a eliminar

        Returns:
            Confirmación de la eliminación
        """
        success = await agent.delete_event(evento_id)
        if success:
            return f"Evento {evento_id} eliminado correctamente."
        return f"Error al eliminar el evento {evento_id}."

    return [obtener_eventos, crear_evento, actualizar_evento, eliminar_evento]