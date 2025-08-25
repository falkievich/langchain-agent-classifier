from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.arrays_tool import (
    listar_todos_los_funcionarios,
    buscar_funcionario_por_nombre,
    listar_todas_las_causas,
    buscar_causa_por_descripcion,
    listar_todas_las_clasificaciones_legajo,
    buscar_clasificacion_legajo_por_descripcion,
)

from funcs.helpers_and_utility.fallback_resolvers_executor import ejecutar_con_resolver # Esta función se encarga de buscar entra todas las opciones si una función de arrays_tool devuelve vacio

# ————— Wrappers LangChain —————

def make_arrays_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre funcionarios,
    causas y clasificaciones de legajo.
    """

    def _listar_todos_los_funcionarios(_: str = ""):
        return listar_todos_los_funcionarios(json_data)

    def _buscar_funcionario_por_nombre(nombre: str):
        # Tipo = "nombre" → si no encuentra, prueba resolver_por_nombre
        return ejecutar_con_resolver(json_data, buscar_funcionario_por_nombre, nombre, tipo="nombre")

    def _listar_todas_las_causas(_: str = ""):
        return listar_todas_las_causas(json_data)

    def _buscar_causa_por_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion
        return ejecutar_con_resolver(json_data, buscar_causa_por_descripcion, descripcion, tipo="descripcion")

    def _listar_todas_las_clasificaciones_legajo(_: str = ""):
        return listar_todas_las_clasificaciones_legajo(json_data)

    def _buscar_clasificacion_legajo_por_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion
        return ejecutar_con_resolver(json_data, buscar_clasificacion_legajo_por_descripcion, descripcion, tipo="descripcion")

    return [
        LangChainTool(
            name="listar_todos_los_funcionarios",
            func=_listar_todos_los_funcionarios,
            description="Lista todos los funcionarios registrados en el legajo."
        ),
        LangChainTool(
            name="buscar_funcionario_por_nombre",
            func=_buscar_funcionario_por_nombre,
            description="Busca funcionarios filtrando SOLAMENTE por nombre."
        ),
        LangChainTool(
            name="listar_todas_las_causas",
            func=_listar_todas_las_causas,
            description="Devuelve todas las causas registradas en el legajo."
        ),
        LangChainTool(
            name="buscar_causa_por_descripcion",
            func=_buscar_causa_por_descripcion,
            description="Busca causas en base a una descripción de la misma."
        ),
        LangChainTool(
            name="listar_todas_las_clasificaciones_legajo",
            func=_listar_todas_las_clasificaciones_legajo,
            description="Devuelve todas las clasificaciones de legajo disponibles."
        ),
        LangChainTool(
            name="buscar_clasificacion_legajo_por_descripcion",
            func=_buscar_clasificacion_legajo_por_descripcion,
            description="Busca clasificaciones de legajo filtrando por una descripción de la misma."
        ),
    ]
