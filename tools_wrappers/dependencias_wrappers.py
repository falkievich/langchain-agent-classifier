from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.dependencias_vistas_tool import (
    listar_todas_las_dependencias,
    buscar_dependencias_por_organismo_codigo,
    buscar_dependencias_por_organismo_descripcion,
    buscar_dependencias_por_codigo,
    buscar_dependencias_por_dependencia_descripcion,
    buscar_dependencias_por_jerarquia,
    buscar_dependencias_por_rol,
    buscar_dependencias_por_tipos,
    buscar_dependencias_por_clase_descripcion,
    buscar_dependencias_por_clase_codigo,
    buscar_dependencias_por_activo,
)

# ————— Wrappers LangChain —————

def make_dependencias_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre dependencias.
    """

    def _listar_todas_las_dependencias(_: str = ""):
        return listar_todas_las_dependencias(json_data)

    def _buscar_dependencias_por_organismo_codigo(codigo: str):
        return buscar_dependencias_por_organismo_codigo(json_data, codigo)

    def _buscar_dependencias_por_organismo_descripcion(descripcion: str):
        return buscar_dependencias_por_organismo_descripcion(json_data, descripcion)

    def _buscar_dependencias_por_codigo(codigo: str):
        return buscar_dependencias_por_codigo(json_data, codigo)

    def _buscar_dependencias_por_dependencia_descripcion(descripcion: str):
        return buscar_dependencias_por_dependencia_descripcion(json_data, descripcion)

    def _buscar_dependencias_por_jerarquia(jerarquia: str):
        return buscar_dependencias_por_jerarquia(json_data, jerarquia)

    def _buscar_dependencias_por_rol(rol: str):
        return buscar_dependencias_por_rol(json_data, rol)

    def _buscar_dependencias_por_tipos(tipos: str):
        return buscar_dependencias_por_tipos(json_data, tipos)

    def _buscar_dependencias_por_clase_descripcion(descripcion: str):
        return buscar_dependencias_por_clase_descripcion(json_data, descripcion)

    def _buscar_dependencias_por_clase_codigo(codigo: str):
        return buscar_dependencias_por_clase_codigo(json_data, codigo)

    def _buscar_dependencias_por_activo(flag: str):
        return buscar_dependencias_por_activo(json_data, flag)

    return [
        LangChainTool(
            name="listar_todas_las_dependencias",
            func=_listar_todas_las_dependencias,
            description="Lista todas las dependencias registradas en el legajo."
        ),
        LangChainTool(
            name="buscar_dependencias_por_organismo_codigo",
            func=_buscar_dependencias_por_organismo_codigo,
            description="Busca dependencias filtrando por el código de organismo."
        ),
        LangChainTool(
            name="buscar_dependencias_por_organismo_descripcion",
            func=_buscar_dependencias_por_organismo_descripcion,
            description="Busca dependencias filtrando por la descripción del organismo."
        ),
        LangChainTool(
            name="buscar_dependencias_por_codigo",
            func=_buscar_dependencias_por_codigo,
            description="Busca dependencias filtrando por su código."
        ),
        LangChainTool(
            name="buscar_dependencias_por_dependencia_descripcion",
            func=_buscar_dependencias_por_dependencia_descripcion,
            description="Busca dependencias filtrando por la descripción de la misma."
        ),
        LangChainTool(
            name="buscar_dependencias_por_jerarquia",
            func=_buscar_dependencias_por_jerarquia,
            description="Busca dependencias filtrando por el código numérico de jerarquía (ejemplo: 1, 2, 3...)."
        ),
        LangChainTool(
            name="buscar_dependencias_por_rol",
            func=_buscar_dependencias_por_rol,
            description="Busca dependencias filtrando por la descripción de un rol."
        ),
        LangChainTool(
            name="buscar_dependencias_por_tipos",
            func=_buscar_dependencias_por_tipos,
            description="Busca dependencias filtrando por tipo."
        ),
        LangChainTool(
            name="buscar_dependencias_por_clase_descripcion",
            func=_buscar_dependencias_por_clase_descripcion,
            description="Busca dependencias filtrando por descripción de clase."
        ),
        LangChainTool(
            name="buscar_dependencias_por_clase_codigo",
            func=_buscar_dependencias_por_clase_codigo,
            description="Busca dependencias filtrando por el código de clase."
        ),
        LangChainTool(
            name="buscar_dependencias_por_activo",
            func=_buscar_dependencias_por_activo,
            description="Filtra dependencias según si están activas o no (valor booleano)."
        ),
    ]
