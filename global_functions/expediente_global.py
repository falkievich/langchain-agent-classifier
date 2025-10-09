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
    "estado_expediente: Devuelve el estado actual del expediente.",
    "materias_expediente: Devuelve la lista de materias jurídicas asociadas.",
    "tipo_expediente: Devuelve el tipo de expediente (civil, penal, laboral, etc.).",
    "numero_expediente: Devuelve el número identificador del expediente.",
    "anio_expediente: Devuelve el año de inicio del expediente.",
    "nivel_acceso_expediente: Devuelve el nivel de acceso (público, privado, etc.).",
    "caratula_publica_expediente: Devuelve la carátula pública del expediente.",
    "caratula_privada_expediente: Devuelve la carátula privada del expediente.",
    "tipo_proceso_expediente: Devuelve el tipo de proceso judicial asociado.",
    "etapa_procesal_expediente: Devuelve la etapa procesal actual (ej: INICIA, TRÁMITE).",
    "cuij_expediente: Devuelve el CUIJ (código único de identificación judicial).",
    "fechas_expediente: Devuelve la fecha de inicio y la última modificación del expediente.",
]


def obtener_dato_expediente(json_data: Dict[str, Any], campo: str) -> Dict[str, Any]:
    """
    Devuelve información del expediente según el campo especificado.
    Si no se encuentra nada, usa el fallback global.

    Campos disponibles: EXPEDIENTE_CAMPOS_DISPONIBLES
    """
    if campo == "estado_expediente":
        res = buscar_estado_expediente(json_data)
    elif campo == "materias_expediente":
        res = buscar_materias_expediente(json_data)
    elif campo == "tipo_expediente":
        res = buscar_tipo_expediente(json_data)
    elif campo == "numero_expediente":
        res = buscar_numero_expediente(json_data)
    elif campo == "anio_expediente":
        res = buscar_anio_expediente(json_data)
    elif campo == "nivel_acceso_expediente":
        res = buscar_nivel_acceso(json_data)
    elif campo == "caratula_publica_expediente":
        res = buscar_caratula_publica(json_data)
    elif campo == "caratula_privada_expediente":
        res = buscar_caratula_privada(json_data)
    elif campo == "tipo_proceso_expediente":
        res = buscar_tipo_proceso(json_data)
    elif campo == "etapa_procesal_expediente":
        res = buscar_etapa_procesal(json_data)
    elif campo == "cuij_expediente":
        res = buscar_cuij(json_data)
    elif campo == "fechas_expediente":
        res = buscar_fechas_inicio_y_modificacion_expediente(json_data)
    else:
        return {
            "error": f"Campo '{campo}' no reconocido en obtener_dato_expediente. "
                     f"Opciones válidas: {EXPEDIENTE_CAMPOS_DISPONIBLES}"
        }

    # if not res or all(not v for v in res.values()):
    #     return buscar_en_json_global(json_data, campo)

    return res