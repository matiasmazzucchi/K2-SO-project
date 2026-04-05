"""
Cliente de Google Calendar para gestión de eventos.
Reemplaza los nodos de N8N de Google Calendar.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import get_settings


class GoogleCalendarClient:
    """
    Cliente para interactuar con Google Calendar API.

    Maneja operaciones CRUD de eventos de calendario,
    con soporte para autenticación via Service Account o OAuth.
    """

    def __init__(self, project_id: str):
        """
        Inicializa el cliente de Google Calendar.

        Args:
            project_id: ID del proyecto de Google Cloud
        """
        self.settings = get_settings()
        self.project_id = project_id
        self._service = None
        self._credentials = None

    def _get_credentials(self):
        """
        Obtiene las credenciales de autenticación.

        Soporta:
        1. Service Account (recomendado para producción)
        2. OAuth2 (para uso interactivo)
        """
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if credentials_path and os.path.exists(credentials_path):
            self._credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            return self._credentials

        raise ValueError(
            "No se encontraron credenciales. Configure GOOGLE_APPLICATION_CREDENTIALS"
        )

    def _get_service(self):
        """Obtiene o crea el servicio de Google Calendar."""
        if self._service is None:
            if self._credentials is None:
                self._credentials = self._get_credentials()
            self._service = build('calendar', 'v3', credentials=self._credentials)
        return self._service

    def is_authenticated(self) -> bool:
        """Verifica si el cliente está autenticado."""
        try:
            self._get_credentials()
            return True
        except Exception:
            return False

    async def get_events(
        self,
        calendar_id: str,
        start: datetime,
        end: datetime,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene eventos del calendario.

        Args:
            calendar_id: ID del calendario
            start: Fecha de inicio
            end: Fecha de fin
            max_results: Máximo número de resultados

        Returns:
            Lista de eventos
        """
        service = self._get_service()

        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Formatear eventos
            formatted_events = []
            for event in events:
                formatted_events.append({
                    "id": event.get("id"),
                    "summary": event.get("summary", "Sin título"),
                    "start": event.get("start", {}),
                    "end": event.get("end", {}),
                    "description": event.get("description", ""),
                    "location": event.get("location", "")
                })

            return formatted_events

        except HttpError as e:
            print(f"Error obteniendo eventos: {e}")
            return []

    async def create_event(
        self,
        calendar_id: str,
        summary: str,
        start: datetime,
        end: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un evento en el calendario.

        Args:
            calendar_id: ID del calendario
            summary: Título del evento
            start: Fecha y hora de inicio
            end: Fecha y hora de fin
            description: Descripción (opcional)
            location: Ubicación (opcional)

        Returns:
            Diccionario con el evento creado
        """
        service = self._get_service()

        event_body = {
            'summary': summary,
            'description': description or '',
            'location': location or '',
            'start': {
                'dateTime': start.isoformat(),
                'timeZone': self.settings.default_timezone
            },
            'end': {
                'dateTime': end.isoformat(),
                'timeZone': self.settings.default_timezone
            }
        }

        try:
            event = service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()

            return {
                "success": True,
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end")
            }

        except HttpError as e:
            print(f"Error creando evento: {e}")
            return {"success": False, "error": str(e)}

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza un evento existente.

        Args:
            calendar_id: ID del calendario
            event_id: ID del evento
            updates: Campos a actualizar

        Returns:
            Diccionario con el evento actualizado
        """
        service = self._get_service()

        try:
            # Primero obtener el evento actual
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            # Actualizar campos
            for key, value in updates.items():
                if key in ['summary', 'description', 'location']:
                    event[key] = value
                elif key == 'start':
                    event['start'] = {
                        'dateTime': value.isoformat(),
                        'timeZone': self.settings.default_timezone
                    }
                elif key == 'end':
                    event['end'] = {
                        'dateTime': value.isoformat(),
                        'timeZone': self.settings.default_timezone
                    }

            # Guardar cambios
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            return {
                "success": True,
                "id": updated_event.get("id"),
                "summary": updated_event.get("summary")
            }

        except HttpError as e:
            print(f"Error actualizando evento: {e}")
            return {"success": False, "error": str(e)}

    async def delete_event(
        self,
        calendar_id: str,
        event_id: str
    ) -> bool:
        """
        Elimina un evento del calendario.

        Args:
            calendar_id: ID del calendario
            event_id: ID del evento

        Returns:
            True si se eliminó correctamente
        """
        service = self._get_service()

        try:
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            return True

        except HttpError as e:
            print(f"Error eliminando evento: {e}")
            return False

    async def get_event(
        self,
        calendar_id: str,
        event_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un evento específico.

        Args:
            calendar_id: ID del calendario
            event_id: ID del evento

        Returns:
            Diccionario con el evento o None
        """
        service = self._get_service()

        try:
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            return {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end"),
                "description": event.get("description"),
                "location": event.get("location")
            }

        except HttpError as e:
            print(f"Error obteniendo evento: {e}")
            return None