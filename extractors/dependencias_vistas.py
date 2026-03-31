"""
extractors/dependencias_vistas.py
─────────────────────────────────
Funciones de extracción para "dependencias_vistas" y sus sub-nodos:
  - tipos
"""
from typing import Any, Dict, List
from funcs.helpers_and_utility.langchain_utility import (
    buscar_entradas_en_lista,
    normalize_and_clean,
    _to_bool_flag,
)

def _deps(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return json_data.get("dependencias_vistas", []) or []

# ═══════════════════════════════════════════════════════════════
#  Nivel 0: lista completa
# ═══════════════════════════════════════════════════════════════

def listar_dependencias(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"dependencias_vistas": _deps(json_data)}

# ═══════════════════════════════════════════════════════════════
#  Nivel 1: búsqueda por campos directos
# ═══════════════════════════════════════════════════════════════

def buscar_dependencia_por_organismo_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["organismo_codigo"], codigo, exact=True)
    return {"dependencias_por_organismo_codigo": matches}

def buscar_dependencia_por_organismo_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["organismo_descripcion"], desc, exact=False)
    return {"dependencias_por_organismo_descripcion": matches}

def buscar_dependencia_por_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["dependencia_codigo"], codigo, exact=True)
    return {"dependencias_por_codigo": matches}

def buscar_dependencia_por_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["dependencia_descripcion"], desc, exact=False)
    return {"dependencias_por_descripcion": matches}

def buscar_dependencia_por_clase_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["clase_codigo"], codigo, exact=True)
    return {"dependencias_por_clase_codigo": matches}

def buscar_dependencia_por_clase_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["clase_descripcion"], desc, exact=False)
    return {"dependencias_por_clase_descripcion": matches}

def buscar_dependencia_por_jerarquia(json_data: Dict[str, Any], jerarquia: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["dependencia_jerarquia"], jerarquia, exact=True)
    return {"dependencias_por_jerarquia": matches}

def buscar_dependencia_por_rol(json_data: Dict[str, Any], rol: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["rol"], rol, exact=True)
    return {"dependencias_por_rol": matches}

def buscar_dependencia_por_activo(json_data: Dict[str, Any], flag: Any) -> Dict[str, Any]:
    b = _to_bool_flag(flag)
    matches = [d for d in _deps(json_data) if bool(d.get("activo", False)) == b]
    return {"dependencias_por_activo": matches}

def buscar_dependencia_por_fecha_desde(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["fecha_desde"], fecha, exact=False)
    return {"dependencias_por_fecha_desde": matches}

def buscar_dependencia_por_fecha_hasta(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "dependencias_vistas",
                                       ["fecha_hasta"], fecha, exact=False)
    return {"dependencias_por_fecha_hasta": matches}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: tipos
# ═══════════════════════════════════════════════════════════════

def listar_tipos_dependencias(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve cada dependencia con su lista de tipos."""
    out = []
    for d in _deps(json_data):
        tipos = d.get("tipos", []) or []
        if tipos:
            out.append({
                "dependencia_descripcion": d.get("dependencia_descripcion"),
                "tipos": tipos,
            })
    return {"tipos_dependencias": out}

def buscar_dependencia_por_tipo_codigo(json_data: Dict[str, Any], tipo_codigo: str) -> Dict[str, Any]:
    """Filtra dependencias que tengan un tipo con el codigo dado."""
    n = normalize_and_clean(tipo_codigo)
    out = []
    for d in _deps(json_data):
        for t in (d.get("tipos") or []):
            if n in normalize_and_clean(str(t.get("tipo_codigo", ""))):
                out.append(d)
                break
    return {"dependencias_por_tipo_codigo": out}

def buscar_dependencia_por_tipo_descripcion(json_data: Dict[str, Any], tipo_desc: str) -> Dict[str, Any]:
    """Filtra dependencias que tengan un tipo con la descripcion dada."""
    n = normalize_and_clean(tipo_desc)
    out = []
    for d in _deps(json_data):
        for t in (d.get("tipos") or []):
            if n in normalize_and_clean(str(t.get("tipo_descripcion", ""))):
                out.append(d)
                break
    return {"dependencias_por_tipo_descripcion": out}
