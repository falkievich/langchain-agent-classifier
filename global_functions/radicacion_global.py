from typing import Any, Dict
from langchain_tools.radicacion_tool import (
    buscar_radicacion_por_organismo_codigo,
    buscar_radicacion_por_organismo_descripcion,
    buscar_radicacion_por_motivo_codigo,
    buscar_radicacion_por_motivo_descripcion,
    buscar_radicacion_por_fecha,
)
from global_functions.json_fallback import buscar_en_json_global

# Lista de filtros válidos para buscar_radicacion
RADICACION_FILTROS_DISPONIBLES = [
    "organismo_codigo",
    "organismo_descripcion",
    "motivo_codigo",
    "motivo_descripcion",
    "fecha",
]


def buscar_radicacion(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de radicaciones según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: RADICACION_FILTROS_DISPONIBLES
    """
    if filtro == "organismo_codigo":
        res = buscar_radicacion_por_organismo_codigo(json_data, valor)
    elif filtro == "organismo_descripcion":
        res = buscar_radicacion_por_organismo_descripcion(json_data, valor)
    elif filtro == "motivo_codigo":
        res = buscar_radicacion_por_motivo_codigo(json_data, valor)
    elif filtro == "motivo_descripcion":
        res = buscar_radicacion_por_motivo_descripcion(json_data, valor)
    elif filtro == "fecha":
        res = buscar_radicacion_por_fecha(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_radicacion. "
                     f"Opciones válidas: {RADICACION_FILTROS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, valor)

    return res