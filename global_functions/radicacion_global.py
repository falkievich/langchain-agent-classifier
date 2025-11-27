from typing import Any, Dict
from langchain_tools.radicacion_tool import (
    buscar_radicacion_por_organismo_codigo,
    buscar_radicacion_por_organismo_descripcion,
    buscar_radicacion_por_motivo_codigo,
    buscar_radicacion_por_motivo_descripcion,
    buscar_radicacion_por_fecha,
)
from global_functions.json_fallback import buscar_en_json_por_dominio

# Lista de filtros válidos para buscar_radicacion
RADICACION_FILTROS_DISPONIBLES = [
    "organismo_codigo_radicacion: Filtra radicaciones por el código exacto del organismo actual (ej: 1C0113).",
    "organismo_descripcion_radicacion: Filtra radicaciones por la descripción textual del organismo actual (ej: Juzgado de Familia Nro.02).",
    "motivo_codigo_radicacion: Filtra radicaciones por el código del motivo actual (ej: MTR001).",
    "motivo_descripcion_radicacion: Filtra radicaciones por la descripción del motivo actual (ej: Radicado Inicial).",
    "fecha_radicacion: Filtra radicaciones por fecha de inicio o fin (formato AAAA-MM-DD).",
]

def buscar_radicacion(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de radicaciones según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: RADICACION_FILTROS_DISPONIBLES
    """
    if filtro == "organismo_codigo_radicacion":
        res = buscar_radicacion_por_organismo_codigo(json_data, valor)
    elif filtro == "organismo_descripcion_radicacion":
        res = buscar_radicacion_por_organismo_descripcion(json_data, valor)
    elif filtro == "motivo_codigo_radicacion":
        res = buscar_radicacion_por_motivo_codigo(json_data, valor)
    elif filtro == "motivo_descripcion_radicacion":
        res = buscar_radicacion_por_motivo_descripcion(json_data, valor)
    elif filtro == "fecha_radicacion":
        res = buscar_radicacion_por_fecha(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_radicacion. "
                     f"Opciones válidas: {RADICACION_FILTROS_DISPONIBLES}"
        }

    if not res or (isinstance(res, dict) and not any(res.values())):
        return {
            "mensaje": "No se encontraron resultados específicos. "
                       "Mostrando coincidencias aproximadas dentro del dominio 'radicaciones'.",
            "fallback": buscar_en_json_por_dominio(json_data, "radicaciones", valor)
        }

    return res