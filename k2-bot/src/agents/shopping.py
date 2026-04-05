"""
Agente de supermercado para comparación de precios.
Maneja la base de datos de precios en Google Sheets.
"""
from typing import List, Dict, Any
from datetime import datetime
import pytz

from langchain_core.tools import tool

from ..config import get_settings, SHEET_NAMES, get_shopping_agent_prompt
from ..tools.sheets_tool import GoogleSheetsClient


class ShoppingAgent:
    """
    Agente especializado en comparación de precios de supermercados.

    Maneja la base de datos de precios y permite
    comparar productos entre diferentes supermercados.
    """

    def __init__(self, project_id: str):
        """
        Inicializa el agente de compras.

        Args:
            project_id: ID del proyecto de Google Cloud
        """
        self.settings = get_settings()
        self.project_id = project_id
        self.sheets_client = GoogleSheetsClient(project_id)

    def is_ready(self) -> bool:
        """Verifica si el agente está listo para operar."""
        return self.sheets_client.is_authenticated()

    async def get_prices(
        self,
        product_name: Optional[str] = None,
        supermarket: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene precios de productos.

        Args:
            product_name: Filtrar por nombre de producto
            supermarket: Filtrar por supermercado

        Returns:
            Lista de precios
        """
        sheet_id = self.settings.sheets_ecosistema_tachi
        sheet_gid = SHEET_NAMES["comparacion_precios"]

        rows = await self.sheets_client.get_rows(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid
        )

        # Filtrar según parámetros
        filtered = []
        for row in rows:
            if product_name and product_name.lower() not in row.get("Producto", "").lower():
                continue
            if supermarket and row.get("Supermercado") != supermarket:
                continue
            filtered.append(row)

        return filtered

    async def add_product_price(
        self,
        product: str,
        price: float,
        supermarket: str
    ) -> Dict[str, Any]:
        """
        Agrega un nuevo precio de producto.

        Args:
            product: Nombre del producto
            price: Precio
            supermarket: Nombre del supermercado

        Returns:
            Resultado de la operación
        """
        tz = pytz.timezone(self.settings.default_timezone)
        now = datetime.now(tz)

        sheet_id = self.settings.sheets_ecosistema_tachi
        sheet_gid = SHEET_NAMES["comparacion_precios"]

        row_data = {
            "Id Producto": str(int(now.timestamp() * 1000)),
            "Fecha": now.strftime("%d/%m/%Y"),
            "Supermercado": supermarket,
            "Precio": str(price),
            "Producto": product
        }

        result = await self.sheets_client.append_row(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid,
            data=row_data
        )

        return {
            "success": result.get("success", False),
            "product": row_data
        }

    async def get_supermarkets(self) -> List[str]:
        """
        Obtiene la lista de supermercados disponibles.

        Returns:
            Lista de supermercados
        """
        sheet_id = self.settings.sheets_ecosistema_tachi
        sheet_gid = SHEET_NAMES["categorias_supermercados"]

        rows = await self.sheets_client.get_rows(
            spreadsheet_id=sheet_id,
            sheet_gid=sheet_gid
        )

        supermarkets = set()
        for row in rows:
            if "supermercado" in row:
                supermarkets.add(row["supermercado"])

        return list(supermarkets)

    async def compare_prices(self, product: str) -> Dict[str, Any]:
        """
        Compara precios de un producto entre supermercados.

        Args:
            product: Nombre del producto

        Returns:
            Comparación de precios
        """
        prices = await self.get_prices(product_name=product)

        if not prices:
            return {
                "product": product,
                "found": False,
                "message": f"No encontré precios para '{product}'"
            }

        # Encontrar el más barato
        cheapest = min(prices, key=lambda x: float(x.get("Precio", 999999)))

        return {
            "product": product,
            "found": True,
            "prices": prices,
            "cheapest": {
                "supermarket": cheapest.get("Supermercado"),
                "price": cheapest.get("Precio")
            }
        }


def create_shopping_tools(agent: ShoppingAgent) -> List:
    """
    Crea las herramientas de LangChain para el agente de compras.

    Args:
        agent: Instancia del agente de compras

    Returns:
        Lista de herramientas
    """

    @tool
    async def comparar_precios(producto: str) -> str:
        """
        Compara precios de un producto entre supermercados.
        Úsalo cuando el usuario quiera saber dónde comprar más barato.

        Args:
            producto: Nombre del producto a comparar

        Returns:
            Comparación de precios
        """
        result = await agent.compare_prices(producto)

        if not result["found"]:
            return result["message"]

        response = f"Precios para '{producto}':\n"
        for price in result["prices"]:
            response += f"- {price.get('Supermercado')}: ${price.get('Precio')}\n"

        cheapest = result["cheapest"]
        response += f"\nMás barato en {cheapest['supermarket']} a ${cheapest['price']}"

        return response

    @tool
    async def agregar_precio_producto(producto: str, precio: float, supermercado: str) -> str:
        """
        Agrega un nuevo precio de producto a la base de datos.
        Úsalo cuando el usuario quiera registrar un precio.

        Args:
            producto: Nombre del producto
            precio: Precio del producto
            supermercado: Nombre del supermercado

        Returns:
            Confirmación del registro
        """
        result = await agent.add_product_price(producto, precio, supermercado)

        if result["success"]:
            return f"Registrado: {producto} a ${precio} en {supermercado}"
        return "Error al registrar el precio."

    @tool
    async def ver_supermercados() -> str:
        """
        Obtiene la lista de supermercados disponibles.
        Úsalo para validar el nombre del supermercado.

        Returns:
            Lista de supermercados
        """
        supermarkets = await agent.get_supermarkets()
        return f"Supermercados disponibles: {', '.join(supermarkets)}"

    return [comparar_precios, agregar_precio_producto, ver_supermercados]