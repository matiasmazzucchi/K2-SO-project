"""
Agente financiero para gestión de egresos.
Maneja las operaciones con Google Sheets.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz

from langchain_core.tools import tool

from ..config import get_settings, SHEET_NAMES, get_financial_agent_prompt
from ..tools.sheets_tool import GoogleSheetsClient


class FinancialAgent:
    """
    Agente especializado en gestión financiera.

    Maneja egresos, categorización y consultas
    de gastos en Google Sheets.
    """

    def __init__(self, project_id: str):
        """
        Inicializa el agente financiero.

        Args:
            project_id: ID del proyecto de Google Cloud
        """
        self.settings = get_settings()
        self.project_id = project_id
        self.sheets_client = GoogleSheetsClient(project_id)

    def is_ready(self) -> bool:
        """Verifica si el agente está listo para operar."""
        return self.sheets_client.is_authenticated()

    async def get_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los egresos registrados.

        Args:
            category: Filtrar por categoría (opcional)
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            Lista de egresos
        """
        # Obtener datos de la hoja de egresos variables
        sheet_id = self.settings.sheets_ecosistema_mazzucchi
        sheet_gid = SHEET_NAMES["egresos_variables"]

        rows = await self.sheets_client.get_rows(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid
        )

        # Filtrar según parámetros
        filtered = []
        for row in rows:
            # Validar filtros
            if category and row.get("categoria") != category:
                continue
            # TODO: Implementar filtro de fechas

            filtered.append(row)

        return filtered

    async def add_expense(
        self,
        category: str,
        amount: float,
        description: str
    ) -> Dict[str, Any]:
        """
        Registra un nuevo egreso.

        Args:
            category: Categoría del gasto
            amount: Monto
            description: Descripción

        Returns:
            Diccionario con el resultado de la operación
        """
        tz = pytz.timezone(self.settings.default_timezone)
        now = datetime.now(tz)

        sheet_id = self.settings.sheets_ecosistema_mazzucchi
        sheet_gid = SHEET_NAMES["egresos_variables"]

        # Crear fila nueva
        row_data = {
            "Id operacion": str(int(now.timestamp() * 1000)),
            "fecha": now.strftime("%d/%m/%Y"),
            "motivo": description,
            "categoria": category,
            "monto": str(amount)
        }

        result = await self.sheets_client.append_row(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid,
            data=row_data
        )

        return {
            "success": result.get("success", False),
            "expense": row_data
        }

    async def get_categories(self) -> List[str]:
        """
        Obtiene las categorías de egresos disponibles.

        Returns:
            Lista de categorías
        """
        sheet_id = self.settings.sheets_ecosistema_mazzucchi
        sheet_gid = SHEET_NAMES["validacion_egresos"]

        rows = await self.sheets_client.get_rows(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid
        )

        # Extraer categorías únicas
        categories = set()
        for row in rows:
            if "categoria" in row:
                categories.add(row["categoria"])

        return list(categories)

    async def get_fixed_expenses(self) -> List[Dict[str, Any]]:
        """
        Obtiene los egresos fijos del mes.

        Returns:
            Lista de egresos fijos
        """
        sheet_id = self.settings.sheets_flujo_dinero
        sheet_gid = SHEET_NAMES["flujo_2025"]

        rows = await self.sheets_client.get_rows(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid
        )

        return rows

    async def add_income(
        self,
        category: str,
        amount: float,
        description: str
    ) -> Dict[str, Any]:
        """
        Registra un nuevo ingreso.

        Args:
            category: Categoría del ingreso
            amount: Monto
            description: Descripción

        Returns:
            Diccionario con el resultado
        """
        tz = pytz.timezone(self.settings.default_timezone)
        now = datetime.now(tz)

        sheet_id = self.settings.sheets_ecosistema_mazzucchi
        sheet_gid = SHEET_NAMES.get("ingresos", 0) # Placeholder si no existe

        row_data = {
            "fecha": now.strftime("%d/%m/%Y"),
            "concepto": description,
            "categoria": category,
            "monto": str(amount)
        }

        result = await self.sheets_client.append_row(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid,
            data=row_data
        )

        return {
            "success": result.get("success", False),
            "income": row_data
        }

    async def get_income(self) -> List[Dict[str, Any]]:
        """
        Obtiene los ingresos registrados.
        """
        sheet_id = self.settings.sheets_ecosistema_mazzucchi
        sheet_gid = SHEET_NAMES.get("ingresos", 0)

        rows = await self.sheets_client.get_rows(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid
        )
        return rows


def create_financial_tools(agent: FinancialAgent) -> List:
    """
    Crea las herramientas de LangChain para el agente financiero.

    Args:
        agent: Instancia del agente financiero

    Returns:
        Lista de herramientas
    """

    @tool
    async def ver_egresos(query: str = "") -> str:
        """
        Consulta los egresos variables registrados.
        Úsalo cuando el usuario pregunte sobre gastos realizados.

        Args:
            query: Consulta opcional para filtrar

        Returns:
            Lista de egresos en formato texto
        """
        expenses = await agent.get_expenses()
        if not expenses:
            return "No hay egresos registrados."

        result = "Egresos variables registrados:\n"
        for exp in expenses[:10]:  # Últimos 10
            result += f"- {exp.get('fecha', 'N/A')}: {exp.get('monto', 'N/A')} - {exp.get('motivo', 'N/A')}\n"
        return result

    @tool
    async def ver_egresos_fijos() -> str:
        """
        Consulta los egresos fijos del mes actual.
        Úsalo cuando el usuario pregunte sobre gastos fijos.

        Returns:
            Lista de egresos fijos en formato texto
        """
        expenses = await agent.get_fixed_expenses()
        if not expenses:
            return "No hay egresos fijos registrados."

        result = "Egresos fijos del mes:\n"
        for exp in expenses[:10]:
            result += f"- {exp.get('concepto', 'N/A')}: {exp.get('monto', 'N/A')}\n"
        return result

    @tool
    async def nuevo_egreso(categoria: str, monto: float, motivo: str) -> str:
        """
        Registra un nuevo egreso en la hoja de cálculo.
        Úsalo cuando el usuario quiera agendar un gasto.

        Args:
            categoria: Categoría del gasto
            monto: Monto del gasto
            motivo: Descripción del gasto
        """
        result = await agent.add_expense(categoria, monto, motivo)
        if result["success"]:
            return f"Egreso registrado: {monto} en {categoria} - {motivo}"
        return "Error al registrar el egreso."

    @tool
    async def categorias_egresos() -> str:
        """
        Obtiene las categorías disponibles para egresos.
        Úsalo para validar categorías antes de registrar.
        """
        categories = await agent.get_categories()
        return f"Categorías disponibles: {', '.join(categories)}"

    @tool
    async def nuevo_ingreso(categoria: str, monto: float, motivo: str) -> str:
        """
        Registra un nuevo ingreso en la hoja de cálculo.
        Úsalo cuando el usuario cobre dinero o reciba un pago.

        Args:
            categoria: Categoría del ingreso
            monto: Monto del ingreso
            motivo: Descripción o concepto
        """
        result = await agent.add_income(categoria, monto, motivo)
        if result["success"]:
            return f"Ingreso registrado: {monto} en {categoria} - {motivo}. ¡Excelente, Matz! Más créditos para el Imperio."
        return "Error al registrar el ingreso."

    @tool
    async def ver_ingresos() -> str:
        """
        Consulta los últimos ingresos registrados.
        """
        incomes = await agent.get_income()
        if not incomes:
            return "No hay ingresos registrados recientemente."
            
        result = "Últimos ingresos registrados:\n"
        for inc in incomes[:10]:
            result += f"- {inc.get('fecha', 'N/A')}: {inc.get('monto', 'N/A')} - {inc.get('concepto', 'N/A')}\n"
        return result

    return [ver_egresos, ver_egresos_fijos, nuevo_egreso, categorias_egresos, nuevo_ingreso, ver_ingresos]