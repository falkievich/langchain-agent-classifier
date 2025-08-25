from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.materia_delitos_tool import (
    listar_todos_los_delitos,
    buscar_delito_por_codigo,
    buscar_delitos_por_descripcion,
    buscar_delito_por_orden,
)

from funcs.helpers_and_utility.fallback_resolvers_executor import ejecutar_con_resolver # Esta función se encarga de buscar entra todas las opciones si una función de materia_delitos_tool devuelve vacio

# ————— Wrappers LangChain —————

def make_materia_delitos_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre 'materia_delitos'.
    """

    def _listar_todos_los_delitos(_: str = ""):
        return listar_todos_los_delitos(json_data)

    def _buscar_delito_por_codigo(codigo: str):
        # Tipo = "codigo" → si no encuentra, prueba resolver_por_codigo
        return ejecutar_con_resolver(json_data, buscar_delito_por_codigo, codigo, tipo="codigo")

    def _buscar_delitos_por_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion
        return ejecutar_con_resolver(json_data, buscar_delitos_por_descripcion, descripcion, tipo="descripcion")

    def _buscar_delito_por_orden(orden: str):
        return buscar_delito_por_orden(json_data, orden)

    return [
        LangChainTool(
            name="listar_todos_los_delitos",
            func=_listar_todos_los_delitos,
            description="Lista todos los delitos disponibles en el legajo." # excluyendo ID´s
        ),
        LangChainTool(
            name="buscar_delito_por_codigo",
            func=_buscar_delito_por_codigo,
            description="Busca un delito en base a su código único numérico."
        ),
        LangChainTool(
            name="buscar_delitos_por_descripcion",
            func=_buscar_delitos_por_descripcion,
            description="Busca delitos a partir de una descripción textual del delito."
        ),
        LangChainTool(
            name="buscar_delito_por_orden",
            func=_buscar_delito_por_orden,
            description="Busca un delito por su número de orden (valor numérico)."
        ),
    ]
