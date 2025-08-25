from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.dependencias_vistas_tool import (
    listar_todas_las_dependencias,
    buscar_dependencias_por_organismo_codigo,
    buscar_dependencias_por_organismo_descripcion,
    buscar_dependencias_por_codigo,
    buscar_dependencias_por_dependencia_descripcion,
    buscar_dependencias_por_clase_codigo,
    buscar_dependencias_por_clase_descripcion,
    buscar_dependencias_por_activo,
    buscar_dependencias_por_jerarquia,
    buscar_dependencias_por_rol,
    buscar_dependencias_por_tipos,
    listar_fechas_depedencias,
    buscar_dependencias_por_fecha,
)

from funcs.helpers_and_utility.fallback_resolvers_executor import ejecutar_con_resolver # Esta función se encarga de buscar entra todas las opciones si una función de dependencias_vistas_tool devuelve vacio

# ————— Wrappers LangChain —————

def make_dependencias_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre dependencias.
    """

    def _listar_todas_las_dependencias(_: str = ""):
        return listar_todas_las_dependencias(json_data)

    def _buscar_dependencias_por_organismo_codigo(codigo: str):
        # Tipo = "codigo" → si no encuentra, prueba resolver_por_codigo
        return ejecutar_con_resolver(json_data, buscar_dependencias_por_organismo_codigo, codigo, tipo="codigo")

    def _buscar_dependencias_por_organismo_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion
        return ejecutar_con_resolver(json_data, buscar_dependencias_por_organismo_descripcion, descripcion, tipo="descripcion")

    def _buscar_dependencias_por_codigo(codigo: str):
        # Tipo = "codigo" → si no encuentra, prueba resolver_por_codigo
        return ejecutar_con_resolver(json_data, buscar_dependencias_por_codigo, codigo, tipo="codigo")

    def _buscar_dependencias_por_dependencia_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion
        return ejecutar_con_resolver(json_data, buscar_dependencias_por_dependencia_descripcion, descripcion, tipo="descripcion")

    def _buscar_dependencias_por_jerarquia(jerarquia: str):
        return buscar_dependencias_por_jerarquia(json_data, jerarquia)

    def _buscar_dependencias_por_rol(rol: str):
        return buscar_dependencias_por_rol(json_data, rol)

    def _buscar_dependencias_por_tipos(tipos: str):
        return buscar_dependencias_por_tipos(json_data, tipos)

    def _buscar_dependencias_por_clase_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion
        return ejecutar_con_resolver(json_data, buscar_dependencias_por_clase_descripcion, descripcion, tipo="descripcion")

    def _buscar_dependencias_por_clase_codigo(codigo: str):
        # Tipo = "codigo" → si no encuentra, prueba resolver_por_codigo
        return ejecutar_con_resolver(json_data, buscar_dependencias_por_clase_codigo, codigo, tipo="codigo")

    def _buscar_dependencias_por_activo(flag: str):
        return buscar_dependencias_por_activo(json_data, flag)

    def _listar_fechas_depedencias(_: str = ""):
        return listar_fechas_depedencias(json_data)

    def _buscar_dependencias_por_fecha(fecha: str):
        return buscar_dependencias_por_fecha(json_data, fecha)

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
        LangChainTool(
            name="listar_fechas_depedencias",
            func=_listar_fechas_depedencias,
            description="Trae todas las fechas de dependecias que hay"
        ),
        LangChainTool(
            name="buscar_dependencias_por_fecha",
            func=_buscar_dependencias_por_fecha,
            description="Busca dependencias a partir de UNA fecha, devolviendo desde cuándo o hasta cuándo el expediente estuvo en la dependencia. El parámetro de fecha debe estar en formato ISO corto: AAAA-MM-DD."
        ),

    ]
