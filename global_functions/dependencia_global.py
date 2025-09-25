from typing import Any, Dict
from langchain_tools.dependencias_vistas_tool import (
    buscar_dependencias_por_organismo_codigo,
    buscar_dependencias_por_organismo_descripcion,
    buscar_dependencias_por_codigo,
    buscar_dependencias_por_dependencia_descripcion,
    buscar_dependencias_por_jerarquia,
    buscar_dependencias_por_rol,
    buscar_dependencias_por_tipos,
    buscar_dependencias_por_clase_descripcion,
    buscar_dependencias_por_clase_codigo,
    buscar_dependencias_por_activo,
    buscar_dependencias_por_fecha,
)
from global_functions.json_fallback import buscar_en_json_global

# Lista de filtros válidos para buscar_dependencia
DEPENDENCIA_FILTROS_DISPONIBLES = [
    "organismo_codigo",
    "organismo_descripcion",
    "codigo",
    "dependencia_descripcion",
    "jerarquia",
    "rol",
    "tipos",
    "clase_descripcion",
    "clase_codigo",
    "activo",
    "fecha",
]


def buscar_dependencia(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de dependencias según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: DEPENDENCIA_FILTROS_DISPONIBLES
    """
    if filtro == "organismo_codigo":
        res = buscar_dependencias_por_organismo_codigo(json_data, valor)
    elif filtro == "organismo_descripcion":
        res = buscar_dependencias_por_organismo_descripcion(json_data, valor)
    elif filtro == "codigo":
        res = buscar_dependencias_por_codigo(json_data, valor)
    elif filtro == "dependencia_descripcion":
        res = buscar_dependencias_por_dependencia_descripcion(json_data, valor)
    elif filtro == "jerarquia":
        res = buscar_dependencias_por_jerarquia(json_data, valor)
    elif filtro == "rol":
        res = buscar_dependencias_por_rol(json_data, valor)
    elif filtro == "tipos":
        res = buscar_dependencias_por_tipos(json_data, valor)
    elif filtro == "clase_descripcion":
        res = buscar_dependencias_por_clase_descripcion(json_data, valor)
    elif filtro == "clase_codigo":
        res = buscar_dependencias_por_clase_codigo(json_data, valor)
    elif filtro == "activo":
        res = buscar_dependencias_por_activo(json_data, valor)
    elif filtro == "fecha":
        res = buscar_dependencias_por_fecha(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_dependencia. "
                     f"Opciones válidas: {DEPENDENCIA_FILTROS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, valor)

    return res