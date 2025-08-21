from funcs.langchain.langchain_utility import buscar_entradas_en_lista
from typing import Any, Dict

# ————— Herramientas (Tools) para extracción de información de Expedientes —————

def obtener_info_general_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve la información general del expediente (todos los campos de cabecera_legajo)."""
    return {"cabecera_legajo": json_data.get("cabecera_legajo", {})}

def buscar_estado_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Retorna únicamente el campo 'estado_expediente' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["estado_expediente"],
        needle=json_data.get("cabecera_legajo", {}).get("estado_expediente", ""),
        exact=True
    )
    return {"estado_expediente": matches}

def buscar_materias_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae la lista de 'materias' asociadas al expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["materias"],
        needle="",  # needle vacío para traer todas
        exact=False
    )
    return {"materias": matches}

def buscar_fechas_clave(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Retorna las fechas principales: inicio, registro, radicación y control."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["fecha_inicio", "fecha_registro", "fecha_radicacion", "fecha_control"],
        needle="",  # needle vacío para traer todas
        exact=False
    )
    return {"fechas_clave": matches}

# ————— Listado Agregado de Funciones —————
ALL_EXPEDIENTES_FUNCS = [
    obtener_info_general_expediente,
    buscar_estado_expediente,
    buscar_materias_expediente,
    buscar_fechas_clave,
]
