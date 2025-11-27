from typing import Dict, Any
from langchain.agents import Tool as LangChainTool
from global_functions.search_globals import (
    buscar_por_codigo_global,
    buscar_por_nombre_global,
    buscar_por_fecha_global,
)


def make_global_search_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para búsquedas globales
    (independientes de un dominio específico).
    """
    return [
        LangChainTool(
            name="buscar_por_codigo_global",
            func=lambda codigo: buscar_por_codigo_global(json_data, codigo),
            description="Busca un valor de código en cualquier dominio (abogados, dependencias, radicaciones, delitos, etc.)."
        ),
        LangChainTool(
            name="buscar_por_nombre_global",
            func=lambda nombre: buscar_por_nombre_global(json_data, nombre),
            description="Busca un valor de nombre en cualquier dominio (abogados, funcionarios, personas)."
        ),
        LangChainTool(
            name="buscar_por_fecha_global",
            func=lambda fecha: buscar_por_fecha_global(json_data, fecha),
            description="Busca un valor de fecha en distintos dominios (personas, radicaciones, dependencias, abogados). El formato debe ser AAAA-MM-DD."
        ),
    ]
