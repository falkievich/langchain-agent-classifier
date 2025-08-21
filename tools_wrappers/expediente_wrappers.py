from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.expediente_tool import (
    obtener_info_general_expediente,
    buscar_estado_expediente,
    buscar_materias_expediente,
    buscar_fechas_clave,
)

# ————— Wrappers LangChain —————

def make_expediente_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre 'expedientes'.
    """

    def _obtener_info_general_expediente(_: str = ""):
        return obtener_info_general_expediente(json_data)

    def _buscar_estado_expediente(_: str = ""):
        return buscar_estado_expediente(json_data)

    def _buscar_materias_expediente(_: str = ""):
        return buscar_materias_expediente(json_data)

    def _buscar_fechas_clave(_: str = ""):
        return buscar_fechas_clave(json_data)

    return [
        LangChainTool(
            name="obtener_info_general_expediente",
            func=_obtener_info_general_expediente,
            description="Devuelve toda la información general del expediente y de la cabecera del legajo."
        ),
        LangChainTool(
            name="buscar_estado_expediente",
            func=_buscar_estado_expediente,
            description="Obtiene y retorna el estado actual del expediente dentro del legajo."
        ),
        LangChainTool(
            name="buscar_materias_expediente",
            func=_buscar_materias_expediente,
            description="Extrae la lista de materias jurídicas asociadas al expediente."
        ),
        LangChainTool(
            name="buscar_fechas_clave",
            func=_buscar_fechas_clave,
            description="Obtiene las fechas principales del expediente: inicio, registro, radicación y control."
        ),
    ]
