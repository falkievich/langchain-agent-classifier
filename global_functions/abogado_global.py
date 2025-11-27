from typing import Any, Dict
from langchain_tools.abogado_tool import (
    buscar_abogado_por_nombre,
    buscar_clientes_de_abogado,
    buscar_abogados_por_cliente,
    buscar_abogado_por_matricula,
    buscar_representados_por_fecha_representacion,
)
from global_functions.json_fallback import buscar_en_json_por_dominio

# Lista de filtros válidos para buscar_abogado
ABOGADO_FILTROS_DISPONIBLES = [
    "nombre_abogado: Busca un abogado por su nombre, apellido o nombre apellido",
    "matricula_abogado: Busca un abogado por su matrícula profesional.",
    "clientes_de_un_abogado: En base al nombre de un abogado devuelve todos sus clientes representados.",
    "abogados_por_cliente: En base al nombre de un cliente devuelve todos los abogados que lo representan",
    "fecha_representacion: Filtra representaciones de abogados por fecha de inicio o fin. Formato: AAAA-MM-DD.",
]

def buscar_abogado(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de abogados según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: ABOGADO_FILTROS_DISPONIBLES
    """
    if filtro == "nombre_abogado":
        res = buscar_abogado_por_nombre(json_data, valor)
    elif filtro == "matricula_abogado":
        res = buscar_abogado_por_matricula(json_data, valor)
    elif filtro == "clientes_de_un_abogado":
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

    if not res or (isinstance(res, dict) and not any(res.values())):
        return {
            "mensaje": "No se encontraron resultados específicos. "
                       "Mostrando coincidencias aproximadas dentro del dominio 'abogados'.",
            "fallback": buscar_en_json_por_dominio(json_data, "abogados", valor)
        }

    return res