"""
extractors/materia_delitos.py
─────────────────────────────
Funciones de extracción para "materia_delitos".
"""
from typing import Any, Dict, List
from funcs.helpers_and_utility.langchain_utility import buscar_entradas_en_lista

def _delitos(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return json_data.get("materia_delitos", []) or []

# ═══════════════════════════════════════════════════════════════
#  Nivel 0: lista completa
# ═══════════════════════════════════════════════════════════════

def listar_delitos(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"materia_delitos": _delitos(json_data)}

# ═══════════════════════════════════════════════════════════════
#  Nivel 1: búsqueda por campos
# ═══════════════════════════════════════════════════════════════

def buscar_delito_por_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "materia_delitos",
                                       ["codigo"], codigo, exact=True)
    return {"delitos_por_codigo": matches}

def buscar_delito_por_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "materia_delitos",
                                       ["descripcion"], desc, exact=False)
    return {"delitos_por_descripcion": matches}

def buscar_delito_por_orden(json_data: Dict[str, Any], orden: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "materia_delitos",
                                       ["orden"], orden, exact=True)
    return {"delitos_por_orden": matches}
