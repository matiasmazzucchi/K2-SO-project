"""
Cliente de Gmail para lectura de emails.
Utiliza Gmail API para obtener y leer mensajes.
"""
import os
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import pytz

from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import get_settings


class GmailClient:
    """
    Cliente para interactuar con Gmail API.

    Maneja operaciones de lectura de correos,
    con soporte para autenticación via OAuth2.
    """

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, project_id: str):
        """
        Inicializa el cliente de Gmail.

        Args:
            project_id: ID del proyecto de Google Cloud
        """
        self.settings = get_settings()
        self.project_id = project_id
        self._service = None
        self._credentials = None

    def _get_credentials(self):
        """
        Obtiene las credenciales de autenticación para Gmail.

        Utiliza OAuth2 con token almacenado o genera flujo de autenticación.
        """
        creds = None
        token_path = os.environ.get("GMAIL_TOKEN_PATH", "token.json")
        credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json")

        # Si existe token almacenado, cargar credenciales
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

        # Si no hay credenciales válidas, iniciar flujo de autenticación
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    raise ValueError(
                        f"No se encontró {credentials_path}. "
                        "Descarga el archivo de credenciales desde Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Guardar token para futuras ejecuciones
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self._credentials = creds
        return creds

    def _get_service(self):
        """Obtiene o crea el servicio de Gmail."""
        if self._service is None:
            if self._credentials is None:
                self._credentials = self._get_credentials()
            self._service = build('gmail', 'v1', credentials=self._credentials)
        return self._service

    def is_authenticated(self) -> bool:
        """Verifica si el cliente está autenticado."""
        try:
            self._get_credentials()
            return True
        except Exception as e:
            print(f"Error de autenticación con Gmail: {e}")
            return False

    async def list_emails(
        self,
        query: str = "is:unread",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Lista emails según criterios de búsqueda.

        Args:
            query: Consulta de Gmail API (ej: "is:unread", "from:usuario@email.com")
            max_results: Cantidad máxima de emails a retornar

        Returns:
            Lista de emails con información básica
        """
        try:
            service = self._get_service()

            # Obtener IDs de mensajes
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = []

            # Obtener detalles de cada mensaje
            for message in messages:
                email_data = self._parse_message(
                    service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                )
                emails.append(email_data)

            return emails

        except HttpError as error:
            print(f"Error al listar emails: {error}")
            return []

    async def get_email(self, message_id: str) -> Dict[str, Any]:
        """
        Obtiene un email específico con su contenido completo.

        Args:
            message_id: ID del mensaje

        Returns:
            Diccionario con detalles del email
        """
        try:
            service = self._get_service()

            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return self._parse_message(message)

        except HttpError as error:
            print(f"Error al obtener email: {error}")
            return {}

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
        return await self.list_emails(query=search_query, max_results=max_results)

    async def get_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene todos los emails sin leer.

        Args:
            max_results: Cantidad máxima de emails

        Returns:
            Lista de emails sin leer
        """
        return await self.list_emails(query="is:unread", max_results=max_results)

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
        query = f"from:{sender_email}"
        return await self.list_emails(query=query, max_results=max_results)

    async def get_emails_by_label(
        self,
        label_name: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene emails de una etiqueta específica.

        Args:
            label_name: Nombre de la etiqueta (ej: "Trabajo", "Personal")
            max_results: Cantidad máxima de emails

        Returns:
            Lista de emails de la etiqueta
        """
        query = f"label:{label_name}"
        return await self.list_emails(query=query, max_results=max_results)

    @staticmethod
    def _parse_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parsea un mensaje de Gmail a formato legible.

        Args:
            message_data: Datos del mensaje de Gmail API

        Returns:
            Diccionario con información del email
        """
        headers = message_data['payload']['headers']
        subject = next(
            (h['value'] for h in headers if h['name'] == 'Subject'),
            "(Sin asunto)"
        )
        sender = next(
            (h['value'] for h in headers if h['name'] == 'From'),
            "(Desconocido)"
        )
        date_str = next(
            (h['value'] for h in headers if h['name'] == 'Date'),
            ""
        )

        # Extraer body
        body = ""
        if 'parts' in message_data['payload']:
            for part in message_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                    break
        else:
            if 'body' in message_data['payload'] and 'data' in message_data['payload']['body']:
                body = base64.urlsafe_b64decode(
                    message_data['payload']['body']['data']
                ).decode('utf-8')

        return {
            "id": message_data['id'],
            "subject": subject,
            "from": sender,
            "date": date_str,
            "body": body[:500],  # Primeros 500 caracteres
            "snippet": message_data['snippet']
        }
