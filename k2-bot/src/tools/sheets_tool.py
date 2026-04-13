"""
Cliente de Google Sheets para operaciones con hojas de cálculo.
Reemplaza los nodos de N8N de Google Sheets.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import get_settings

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """
    Cliente para interactuar con Google Sheets API.

    Maneja operaciones CRUD en hojas de cálculo de Google,
    con soporte para autenticación via Service Account o OAuth.
    """

    def __init__(self, project_id: str):
        """
        Inicializa el cliente de Google Sheets.

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
        1. Service Account (vía GOOGLE_APPLICATION_CREDENTIALS)
        2. Application Default Credentials (ADC - para Cloud Run)
        """
        # 1. Intentar cargar Service Account desde archivo
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if credentials_path and os.path.exists(credentials_path):
            try:
                self._credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                logger.info(f"✅ Usando service account desde: {credentials_path}")
                return self._credentials
            except Exception as e:
                logger.warning(f"⚠️ Error cargando service account desde archivo: {e}")

        # 2. Intentar Application Default Credentials (ADC)
        try:
            import google.auth
            credentials, project = google.auth.default(
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self._credentials = credentials
            logger.info("✅ Usando Application Default Credentials (ADC)")
            return self._credentials
        except Exception as e:
            logger.error(f"❌ Error al obtener Application Default Credentials: {e}")

        raise ValueError(
            "No se encontraron credenciales válidas (archivo o ADC). "
            "Configure GOOGLE_APPLICATION_CREDENTIALS o asegúrese de que el entorno tenga acceso IAM."
        )

    def _get_service(self):
        """Obtiene o crea el servicio de Google Sheets."""
        if self._service is None:
            if self._credentials is None:
                self._credentials = self._get_credentials()
            self._service = build('sheets', 'v4', credentials=self._credentials)
        return self._service

    def _get_sheet_name(self, spreadsheet_id: str, sheet_gid: int) -> str:
        """
        Obtiene el nombre de una hoja a partir de su GID.
        """
        service = self._get_service()
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['sheetId'] == sheet_gid:
                return sheet['properties']['title']

        raise ValueError(f"No se encontró la hoja con GID {sheet_gid}")

    def is_authenticated(self) -> bool:
        """Verifica si el cliente está autenticado."""
        try:
            self._get_credentials()
            return True
        except Exception:
            return False

    async def get_rows(
        self,
        spreadsheet_id: str,
        sheet_gid: int,
        range_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene filas de una hoja de cálculo.

        Args:
            spreadsheet_id: ID del spreadsheet
            sheet_gid: GID de la hoja
            range_name: Rango específico (opcional)

        Returns:
            Lista de diccionarios con los datos
        """
        service = self._get_service()
        sheet_name = self._get_sheet_name(spreadsheet_id, sheet_gid)

        try:
            if range_name:
                range_to_read = f"{sheet_name}!{range_name}"
            else:
                # Leer toda la hoja (basado en el nombre)
                range_to_read = sheet_name

            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_to_read
            ).execute()

            values = result.get('values', [])

            if not values:
                return []

            # Primera fila como headers
            headers = values[0]
            rows = []

            for row in values[1:]:
                # Crear diccionario con headers
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row[i] if i < len(row) else ""
                rows.append(row_dict)

            return rows

        except HttpError as e:
            logger.error(f"Error leyendo Google Sheets: {e}")
            return []

    async def append_row(
        self,
        spreadsheet_id: str,
        sheet_gid: int,
        data: Dict[str, Any],
        range_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega una fila a una hoja de cálculo.

        Args:
            spreadsheet_id: ID del spreadsheet
            sheet_gid: GID de la hoja
            data: Diccionario con los datos
            range_name: Rango específico (opcional)

        Returns:
            Resultado de la operación
        """
        service = self._get_service()
        sheet_name = self._get_sheet_name(spreadsheet_id, sheet_gid)

        try:
            # Obtener headers existentes
            if not range_name:
                request_range = f"{sheet_name}!A1:Z1"
            else:
                request_range = f"{sheet_name}!{range_name}"

            headers_result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=request_range
            ).execute()

            headers = headers_result.get('values', [[]])[0]

            # Crear fila en orden de headers
            row_values = [data.get(header, "") for header in headers]

            # Agregar fila
            body = {
                'values': [row_values]
            }

            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=request_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            return {
                "success": True,
                "updated_range": result.get('updates', {}).get('updatedRange')
            }

        except HttpError as e:
            logger.error(f"Error agregando fila a Google Sheets: {e}")
            return {"success": False, "error": str(e)}

    async def update_row(
        self,
        spreadsheet_id: str,
        sheet_gid: int,
        row_index: int,
        data: Dict[str, Any],
        range_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Actualiza una fila en una hoja de cálculo.

        Args:
            spreadsheet_id: ID del spreadsheet
            sheet_gid: GID de la hoja
            row_index: Índice de la fila
            data: Diccionario con los datos
            range_name: Rango específico (opcional)

        Returns:
            Resultado de la operación
        """
        service = self._get_service()
        sheet_name = self._get_sheet_name(spreadsheet_id, sheet_gid)

        try:
            # Obtener headers
            if not range_name:
                request_range = f"{sheet_name}!A1:Z1"
            else:
                request_range = f"{sheet_name}!{range_name}"

            headers_result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=request_range
            ).execute()

            headers = headers_result.get('values', [[]])[0]

            # Crear fila en orden
            row_values = [data.get(header, "") for header in headers]

            # Actualizar fila específica
            update_range = f"{sheet_name}!A{row_index}:{chr(65 + len(headers))}{row_index}"

            body = {
                'values': [row_values]
            }

            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=update_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            return {
                "success": True,
                "updated_cells": result.get('updatedCells')
            }

        except HttpError as e:
            logger.error(f"Error actualizando fila en Google Sheets: {e}")
            return {"success": False, "error": str(e)}

    async def delete_row(
        self,
        spreadsheet_id: str,
        sheet_gid: int,
        row_index: int
    ) -> Dict[str, Any]:
        """
        Elimina una fila de una hoja de cálculo.

        Args:
            spreadsheet_id: ID del spreadsheet
            sheet_gid: GID de la hoja
            row_index: Índice de la fila

        Returns:
            Resultado de la operación
        """
        service = self._get_service()

        try:
            # Obtener metadata de la hoja
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()

            sheet_id = None
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['sheetId'] == sheet_gid:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                return {"success": False, "error": "Sheet not found"}

            # Eliminar fila
            requests = [{
                'deleteDimension': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'ROWS',
                        'startIndex': row_index - 1,
                        'endIndex': row_index
                    }
                }
            }]

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

            return {"success": True}

        except HttpError as e:
            print(f"Error eliminando fila en Google Sheets: {e}")
            return {"success": False, "error": str(e)}