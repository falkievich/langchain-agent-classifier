from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.radicacion_tool import (
    listar_todas_las_radicaciones_y_movimiento_expediente,
    buscar_radicacion_por_organismo_codigo,
    buscar_radicacion_por_organismo_descripcion,
    listar_todas_las_fechas_radicaciones,
    buscar_radicacion_por_fecha,
    buscar_radicacion_por_motivo_codigo,
    buscar_radicacion_por_motivo_descripcion,
)

from funcs.helpers_and_utility.fallback_resolvers_executor import ejecutar_con_resolver # Esta función se encarga de buscar entra todas las opciones si una función de radicacion_tool devuelve vacio

# ————— Wrappers LangChain —————

def make_radicacion_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre 'radicaciones'.
    """

    def _listar_todas_las_radicaciones(_: str = ""):
        return listar_todas_las_radicaciones_y_movimiento_expediente(json_data)

    def _buscar_radicacion_por_organismo_codigo(codigo: str):
        # Tipo = "codigo" → si no encuentra, prueba resolver_por_codigo → luego resolver_por_radicacion
        return ejecutar_con_resolver(json_data, buscar_radicacion_por_organismo_codigo, codigo, tipo="codigo")

    def _buscar_radicacion_por_organismo_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion → luego resolver_por_radicacion
        return ejecutar_con_resolver(json_data, buscar_radicacion_por_organismo_descripcion, descripcion, tipo="descripcion")

    def _buscar_radicacion_por_fecha(fecha: str):
        return buscar_radicacion_por_fecha(json_data, fecha)
    
    def _listar_todas_las_fechas_radicaciones(_: str = ""):
        return listar_todas_las_fechas_radicaciones(json_data)

    def _buscar_radicacion_por_motivo_codigo(codigo: str):
        # Tipo = "codigo" → si no encuentra, prueba resolver_por_codigo → luego resolver_por_radicacion
        return ejecutar_con_resolver(json_data, buscar_radicacion_por_motivo_codigo, codigo, tipo="codigo")

    def _buscar_radicacion_por_motivo_descripcion(descripcion: str):
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion → luego resolver_por_radicacion
        return ejecutar_con_resolver(json_data, buscar_radicacion_por_motivo_descripcion, descripcion, tipo="descripcion")

    return [
        LangChainTool(
            name="listar_todas_las_radicaciones_y_movimiento_expediente",
            func=_listar_todas_las_radicaciones,
            description="Lista todas las radicaciones y movimientos asociados al expediente" # excluyendo ID´s
        ),
        LangChainTool(
            name="buscar_radicacion_por_organismo_codigo",
            func=_buscar_radicacion_por_organismo_codigo,
            description="Busca radicaciones filtrando por el código exacto del organismo actual (valor numérico o alfanumérico)."
        ),
        LangChainTool(
            name="buscar_radicacion_por_organismo_descripcion",
            func=_buscar_radicacion_por_organismo_descripcion,
            description="Busca radicaciones a partir de la descripción del organismo actual (Por ejemplo, Juzgado de Familia Nro.02)."
        ),
        LangChainTool(
            name="listar_todas_las_fechas_radicaciones",
            func=_listar_todas_las_fechas_radicaciones,
            description="Trae todas las fechas de todas las radicaciones."
        ),
        LangChainTool(
            name="buscar_radicacion_por_fecha",
            func=_buscar_radicacion_por_fecha,
            description="Busca radicaciones cuya fecha coincida con la de inicio o la de finalización de la radicación. El parámetro de fecha debe estar en formato ISO corto: AAAA-MM-DD."
        ),
        LangChainTool(
            name="buscar_radicacion_por_motivo_codigo",
            func=_buscar_radicacion_por_motivo_codigo,
            description="Busca radicaciones filtrando por el código del motivo actual (valor numérico o alfanumérico)."
        ),
        LangChainTool(
            name="buscar_radicacion_por_motivo_descripcion",
            func=_buscar_radicacion_por_motivo_descripcion,
            description="Busca radicaciones a partir de la descripción textual del motivo actual de radicación."
        ),
    ]
