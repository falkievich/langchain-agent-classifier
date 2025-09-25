from typing import Any, Dict
from langchain_tools.abogado_tool import (
    buscar_abogado_por_nombre,
    buscar_clientes_de_abogado,
    buscar_abogados_por_cliente,
    buscar_abogado_por_matricula,
    buscar_representados_por_fecha_representacion,
)
from global_functions.json_fallback import buscar_en_json_global

# Lista de filtros válidos para buscar_abogado
ABOGADO_FILTROS_DISPONIBLES = [
    "nombre",
    "matricula",
    "clientes",
    "abogados_por_cliente",
    "fecha_representacion",
]


def buscar_abogado(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de abogados según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: ABOGADO_FILTROS_DISPONIBLES
    """
    if filtro == "nombre":
        res = buscar_abogado_por_nombre(json_data, valor)
    elif filtro == "matricula":
        res = buscar_abogado_por_matricula(json_data, valor)
    elif filtro == "clientes":
        res = buscar_clientes_de_abogado(json_data, valor)
    elif filtro == "abogados_por_cliente":
        res = buscar_abogados_por_cliente(json_data, valor)
    elif filtro == "fecha_representacion":
        res = buscar_representados_por_fecha_representacion(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_abogado. "
                     f"Opciones válidas: {ABOGADO_FILTROS_DISPONIBLES}"
        }

    if not res or all(not v for v in res.values()):
        return buscar_en_json_global(json_data, valor)

    return res