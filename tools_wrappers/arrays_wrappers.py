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

# ————— Wrappers LangChain —————

def make_arrays_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre funcionarios,
    causas y clasificaciones de legajo.
    """

    def _listar_todos_los_funcionarios(_: str = ""):
        return listar_todos_los_funcionarios(json_data)

    def _buscar_funcionario_por_nombre(nombre: str):
        return buscar_funcionario_por_nombre(json_data, nombre)

    def _listar_todas_las_causas(_: str = ""):
        return listar_todas_las_causas(json_data)

    def _buscar_causa_por_descripcion(descripcion: str):
        return buscar_causa_por_descripcion(json_data, descripcion)

    def _listar_todas_las_clasificaciones_legajo(_: str = ""):
        return listar_todas_las_clasificaciones_legajo(json_data)

    def _buscar_clasificacion_legajo_por_descripcion(descripcion: str):
        return buscar_clasificacion_legajo_por_descripcion(json_data, descripcion)

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
