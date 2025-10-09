from typing import Any, Dict
from langchain_tools.materia_delitos_tool import (
    buscar_delito_por_codigo,
    buscar_delitos_por_descripcion,
    buscar_delito_por_orden,
)
from global_functions.json_fallback import buscar_en_json_global

# Lista de filtros válidos para buscar_delito
DELITO_FILTROS_DISPONIBLES = [
    "codigo_delito: Filtra delitos por su código único numérico.",
    "descripcion_delito: Filtra delitos por la descripción textual del delito.",
    "orden_delito: Filtra delitos por su número de orden (valor numérico).",
]


def buscar_delito(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de delitos según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: DELITO_FILTROS_DISPONIBLES
    """
    if filtro == "codigo_delito":
        res = buscar_delito_por_codigo(json_data, valor)
    elif filtro == "descripcion_delito":
        res = buscar_delitos_por_descripcion(json_data, valor)
    elif filtro == "orden_delito":
        res = buscar_delito_por_orden(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_delito. "
                     f"Opciones válidas: {DELITO_FILTROS_DISPONIBLES}"
        }

    # if not res or all(not v for v in res.values()):
    #     return buscar_en_json_global(json_data, valor)

    return res