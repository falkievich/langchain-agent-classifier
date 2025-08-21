from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.radicacion_tool import (
    listar_todas_las_radicaciones_y_movimiento_expediente,
    buscar_radicacion_por_organismo_codigo,
    buscar_radicacion_por_organismo_descripcion,
    buscar_radicacion_por_fecha,
    buscar_radicacion_por_motivo_codigo,
    buscar_radicacion_por_motivo_descripcion,
)

# ————— Wrappers LangChain —————

def make_radicacion_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre 'radicaciones'.
    """

    def _listar_todas_las_radicaciones(_: str = ""):
        return listar_todas_las_radicaciones_y_movimiento_expediente(json_data)

    def _buscar_radicacion_por_organismo_codigo(codigo: str):
        return buscar_radicacion_por_organismo_codigo(json_data, codigo)

    def _buscar_radicacion_por_organismo_descripcion(descripcion: str):
        return buscar_radicacion_por_organismo_descripcion(json_data, descripcion)

    def _buscar_radicacion_por_fecha(fecha: str):
        return buscar_radicacion_por_fecha(json_data, fecha)

    def _buscar_radicacion_por_motivo_codigo(codigo: str):
        return buscar_radicacion_por_motivo_codigo(json_data, codigo)

    def _buscar_radicacion_por_motivo_descripcion(descripcion: str):
        return buscar_radicacion_por_motivo_descripcion(json_data, descripcion)

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
            name="buscar_radicacion_por_fecha",
            func=_buscar_radicacion_por_fecha,
            description="Filtra radicaciones cuyo campo fecha_desde o fecha_hasta contenga la fecha indicada." # MODIFICAR
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
