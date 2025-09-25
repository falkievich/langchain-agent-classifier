from typing import Any, Dict
from langchain_tools.expediente_tool import (
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
from global_functions.json_fallback import buscar_en_json_global

# Campos válidos para obtener_dato_expediente
EXPEDIENTE_CAMPOS_DISPONIBLES = [
    "estado",
    "materias",
    "tipo",
    "numero",
    "anio",
    "nivel_acceso",
    "caratula_publica",
    "caratula_privada",
    "tipo_proceso",
    "etapa_procesal",
    "cuij",
    "fechas_inicio_modificacion",
]


def obtener_dato_expediente(json_data: Dict[str, Any], campo: str) -> Dict[str, Any]:
    """
    Devuelve información del expediente según el campo especificado.
    Si no se encuentra nada, usa el fallback global.

    Campos disponibles: EXPEDIENTE_CAMPOS_DISPONIBLES
    """
    if campo == "estado":
        res = buscar_estado_expediente(json_data)
    elif campo == "materias":
        res = buscar_materias_expediente(json_data)
    elif campo == "tipo":
        res = buscar_tipo_expediente(json_data)
    elif campo == "numero":
        res = buscar_numero_expediente(json_data)
    elif campo == "anio":
        res = buscar_anio_expediente(json_data)
    elif campo == "nivel_acceso":
        res = buscar_nivel_acceso(json_data)
    elif campo == "caratula_publica":
        res = buscar_caratula_publica(json_data)
    elif campo == "caratula_privada":
        res = buscar_caratula_privada(json_data)
    elif campo == "tipo_proceso":
        res = buscar_tipo_proceso(json_data)
    elif campo == "etapa_procesal":
        res = buscar_etapa_procesal(json_data)
    elif campo == "cuij":
        res = buscar_cuij(json_data)
    elif campo == "fechas_inicio_modificacion":
        res = buscar_fechas_inicio_y_modificacion_expediente(json_data)
    else:
        return {
            "error": f"Campo '{campo}' no reconocido en obtener_dato_expediente. "
                     f"Opciones válidas: {EXPEDIENTE_CAMPOS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, campo)

    return res