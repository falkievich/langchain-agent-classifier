"""
extractors/radicaciones.py
──────────────────────────
Funciones de extracción para "radicaciones".
"""
from typing import Any, Dict, List
from funcs.helpers_and_utility.langchain_utility import buscar_entradas_en_lista

def _rads(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return json_data.get("radicaciones", []) or []

# ═══════════════════════════════════════════════════════════════
#  Nivel 0: lista completa
# ═══════════════════════════════════════════════════════════════

def listar_radicaciones(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"radicaciones": _rads(json_data)}

# ═══════════════════════════════════════════════════════════════
#  Nivel 1: búsqueda por campos
# ═══════════════════════════════════════════════════════════════

def buscar_radicacion_por_organismo_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones",
                                       ["organismo_actual_codigo"], codigo, exact=True)
    return {"radicaciones_por_organismo_codigo": matches}

def buscar_radicacion_por_organismo_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones",
                                       ["organismo_actual_descripcion"], desc, exact=False)
    return {"radicaciones_por_organismo_descripcion": matches}

def buscar_radicacion_por_motivo_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones",
                                       ["motivo_actual_codigo"], codigo, exact=True)
    return {"radicaciones_por_motivo_codigo": matches}

def buscar_radicacion_por_motivo_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones",
                                       ["motivo_actual_descripcion"], desc, exact=False)
    return {"radicaciones_por_motivo_descripcion": matches}

def buscar_radicacion_por_fecha_desde(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones",
                                       ["fecha_desde"], fecha, exact=False)
    return {"radicaciones_por_fecha_desde": matches}

def buscar_radicacion_por_fecha_hasta(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones",
                                       ["fecha_hasta"], fecha, exact=False)
    return {"radicaciones_por_fecha_hasta": matches}
