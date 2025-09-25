from typing import Any, Dict
from langchain_tools.arrays_tool import (
    buscar_funcionario_por_nombre,
    buscar_causa_por_descripcion,
    buscar_clasificacion_legajo_por_descripcion,
)
from global_functions.json_fallback import buscar_en_json_global

# Filtros válidos por dominio pequeño
FUNCIONARIO_FILTROS_DISPONIBLES = ["nombre"]
CAUSA_FILTROS_DISPONIBLES = ["descripcion"]
CLASIFICACION_LEGAJO_FILTROS_DISPONIBLES = ["descripcion"]


def buscar_funcionario(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de funcionarios según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: FUNCIONARIO_FILTROS_DISPONIBLES
    """
    if filtro == "nombre":
        res = buscar_funcionario_por_nombre(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_funcionario. "
                     f"Opciones válidas: {FUNCIONARIO_FILTROS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, valor)

    return res


def buscar_causa(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de causas según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: CAUSA_FILTROS_DISPONIBLES
    """
    if filtro == "descripcion":
        res = buscar_causa_por_descripcion(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_causa. "
                     f"Opciones válidas: {CAUSA_FILTROS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, valor)

    return res


def buscar_clasificacion_legajo(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de clasificaciones de legajo según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: CLASIFICACION_LEGAJO_FILTROS_DISPONIBLES
    """
    if filtro == "descripcion":
        res = buscar_clasificacion_legajo_por_descripcion(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_clasificacion_legajo. "
                     f"Opciones válidas: {CLASIFICACION_LEGAJO_FILTROS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, valor)

    return res