from typing import Any, Dict
from langchain_tools.persona_legajo_tool import (
    buscar_persona_por_numero_documento_dni,
    buscar_persona_por_numero_cuil,
    buscar_persona_por_rol,
    buscar_persona_por_descripcion_vinculo,
    buscar_persona_por_codigo_vinculo,
    buscar_persona_por_nombre,
    buscar_persona_por_tipo_documento,
    buscar_persona_por_estado_detencion,
    buscar_persona_por_fecha_nacimiento,
    buscar_persona_por_fecha_participacion,
    buscar_persona_por_fecha_vinculo,
)
from global_functions.json_fallback import buscar_en_json_global

# Lista de filtros válidos para buscar_persona
PERSONA_FILTROS_DISPONIBLES = [
    "dni",
    "cuil",
    "nombre",
    "rol",
    "descripcion_vinculo",
    "codigo_vinculo",
    "tipo_documento",
    "estado_detencion",
    "fecha_nacimiento",
    "fecha_participacion",
    "fecha_vinculo",
]


def buscar_persona(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de personas en el legajo según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: PERSONA_FILTROS_DISPONIBLES
    """
    if filtro == "dni":
        res = buscar_persona_por_numero_documento_dni(json_data, valor)
    elif filtro == "cuil":
        res = buscar_persona_por_numero_cuil(json_data, valor)
    elif filtro == "nombre":
        res = buscar_persona_por_nombre(json_data, valor)
    elif filtro == "rol":
        res = buscar_persona_por_rol(json_data, valor)
    elif filtro == "descripcion_vinculo":
        res = buscar_persona_por_descripcion_vinculo(json_data, valor)
    elif filtro == "codigo_vinculo":
        res = buscar_persona_por_codigo_vinculo(json_data, valor)
    elif filtro == "tipo_documento":
        res = buscar_persona_por_tipo_documento(json_data, valor)
    elif filtro == "estado_detencion":
        res = buscar_persona_por_estado_detencion(json_data, valor)
    elif filtro == "fecha_nacimiento":
        res = buscar_persona_por_fecha_nacimiento(json_data, valor)
    elif filtro == "fecha_participacion":
        res = buscar_persona_por_fecha_participacion(json_data, valor)
    elif filtro == "fecha_vinculo":
        res = buscar_persona_por_fecha_vinculo(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_persona. "
                     f"Opciones válidas: {PERSONA_FILTROS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, valor)

    return res