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
from global_functions.json_fallback import buscar_en_json_por_dominio

# Lista de filtros válidos para buscar_persona
PERSONA_FILTROS_DISPONIBLES = [
    "dni_persona: Busca personas por DNI (7-8 dígitos con o sin puntos).",
    "cuil_persona: Busca personas por CUIL (11 dígitos con o sin guiones/puntos).",
    "nombre_persona: Busca personas por nombre, apellido o nombre completo.",
    "rol_persona: Filtra personas según su rol en el expediente (ej: ACTOR, DEMANDADO).",
    "descripcion_vinculo_persona: Filtra personas por la descripción de su vínculo (ej: Abogado patrocinante).",
    "codigo_vinculo_persona: Filtra personas por el código único del vínculo.",
    "tipo_documento_persona: Filtra personas por tipo de documento (DNI, Pasaporte, etc.).",
    "estado_detencion_persona: Filtra personas según si están detenidas o no (true/false).",
    "fecha_nacimiento_persona: Filtra personas por su fecha de nacimiento exacta (AAAA-MM-DD).",
    "fecha_participacion_persona: Filtra personas por su fecha de participación en el caso (AAAA-MM-DD).",
    "fecha_vinculo_persona: Filtra personas por la fecha de inicio o fin de su vínculo con el expediente (AAAA-MM-DD).",
]

def buscar_persona(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de personas en el legajo según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: PERSONA_FILTROS_DISPONIBLES
    """
    if filtro == "dni_persona":
        res = buscar_persona_por_numero_documento_dni(json_data, valor)
    elif filtro == "cuil_persona":
        res = buscar_persona_por_numero_cuil(json_data, valor)
    elif filtro == "nombre_persona":
        res = buscar_persona_por_nombre(json_data, valor)
    elif filtro == "rol_persona":
        res = buscar_persona_por_rol(json_data, valor)
    elif filtro == "descripcion_vinculo_persona":
        res = buscar_persona_por_descripcion_vinculo(json_data, valor)
    elif filtro == "codigo_vinculo_persona":
        res = buscar_persona_por_codigo_vinculo(json_data, valor)
    elif filtro == "tipo_documento_persona":
        res = buscar_persona_por_tipo_documento(json_data, valor)
    elif filtro == "estado_detencion_persona":
        res = buscar_persona_por_estado_detencion(json_data, valor)
    elif filtro == "fecha_nacimiento_persona":
        res = buscar_persona_por_fecha_nacimiento(json_data, valor)
    elif filtro == "fecha_participacion_persona":
        res = buscar_persona_por_fecha_participacion(json_data, valor)
    elif filtro == "fecha_vinculo_persona":
        res = buscar_persona_por_fecha_vinculo(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_persona. "
                     f"Opciones válidas: {PERSONA_FILTROS_DISPONIBLES}"
        }

    if not res or (isinstance(res, dict) and not any(res.values())):
        return {
            "mensaje": "No se encontraron resultados específicos. "
                       "Mostrando coincidencias aproximadas dentro del dominio 'personas'.",
            "fallback": buscar_en_json_por_dominio(json_data, "personas", valor)
        }

    return res