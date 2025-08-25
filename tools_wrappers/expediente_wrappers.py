from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.expediente_tool import (
    obtener_info_general_expediente,
    buscar_estado_expediente,
    buscar_materias_expediente,
    buscar_tipo_expediente,
    buscar_numero_expediente,
    buscar_anio_expediente,
    buscar_nivel_acceso,
    buscar_caratula_publica,
    buscar_caratula_privada,
    buscar_tipo_proceso,
    buscar_etapa_procesal,
    buscar_cuij,
    buscar_fechas_inicio_y_modificacion_expediente,
)

from funcs.helpers_and_utility.fallback_resolvers_executor import ejecutar_con_resolver # Esta función se encarga de buscar entra todas las opciones si una función de expediente_tool devuelve vacio

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

    def _buscar_tipo_expediente(_: str = ""):
        return buscar_tipo_expediente(json_data)

    def _buscar_numero_expediente(_: str = ""):
        return buscar_numero_expediente(json_data)

    def _buscar_anio_expediente(_: str = ""):
        return buscar_anio_expediente(json_data)

    def _buscar_nivel_acceso(_: str = ""):
        return buscar_nivel_acceso(json_data)

    def _buscar_caratula_publica(_: str = ""):
        return buscar_caratula_publica(json_data)

    def _buscar_caratula_privada(_: str = ""):
        return buscar_caratula_privada(json_data)

    def _buscar_tipo_proceso(_: str = ""):
        return buscar_tipo_proceso(json_data)

    def _buscar_etapa_procesal(_: str = ""):
        return buscar_etapa_procesal(json_data)

    def _buscar_cuij(_: str = ""):
        return buscar_cuij(json_data)

    def _buscar_fechas_inicio_y_modificacion_expediente(_: str = ""):
        return buscar_fechas_inicio_y_modificacion_expediente(json_data)

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
            name="buscar_tipo_expediente",
            func=_buscar_tipo_expediente,
            description="Devuelve el tipo de expediente (ejemplo: civil, penal, laboral, etc.)."
        ),
        LangChainTool(
            name="buscar_numero_expediente",
            func=_buscar_numero_expediente,
            description="Obtiene el número identificador del expediente."
        ),
        LangChainTool(
            name="buscar_anio_expediente",
            func=_buscar_anio_expediente,
            description="Obtiene el año de iniciación del expediente."
        ),
        LangChainTool(
            name="buscar_nivel_acceso",
            func=_buscar_nivel_acceso,
            description="Indica el nivel de acceso asignado al expediente (público, privado, etc.)."
        ),
        LangChainTool(
            name="buscar_caratula_publica",
            func=_buscar_caratula_publica,
            description="Devuelve la carátula pública del expediente."
        ),
        LangChainTool(
            name="buscar_caratula_privada",
            func=_buscar_caratula_privada,
            description="Devuelve la carátula privada del expediente."
        ),
        LangChainTool(
            name="buscar_tipo_proceso",
            func=_buscar_tipo_proceso,
            description="Devuelve el tipo de proceso judicial aplicable del expediente." 
        ),
        LangChainTool(
            name="buscar_etapa_procesal",
            func=_buscar_etapa_procesal,
            description="Devuelve la etapa procesal actual en la que se encuentra el expediente (ejemplo: INICIA, TRAMITE, etc)."
        ),
        LangChainTool(
            name="buscar_cuij",
            func=_buscar_cuij,
            description="Devuelve el código único de identificación judicial (CUIJ) del expediente."
        ),
        LangChainTool(
            name="buscar_fechas_inicio_y_modificacion_expediente",
            func=_buscar_fechas_inicio_y_modificacion_expediente,
            description="Devuelve siempre las fechas clave del expediente: la Fecha de Inicio del Proceso Judicial y la Fecha de la última modificación del expediente (NO SE LE PASAN PARÁMETROS)"
        ),
    ]
