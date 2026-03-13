"""
extractors/extras.py
────────────────────
Funciones de extracción para nodos adicionales del JSON raíz:
  - clasificadores_legajo
  - organismo_control
  - seguridad
  - campos sueltos de raíz (clave_causa, codigo_sistema, etc.)
"""
from typing import Any, Dict, List
from funcs.helpers_and_utility.langchain_utility import normalize_and_clean

# ═══════════════════════════════════════════════════════════════
#  clasificadores_legajo
# ═══════════════════════════════════════════════════════════════

def listar_clasificadores_legajo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"clasificadores_legajo": json_data.get("clasificadores_legajo", [])}

def buscar_clasificador_por_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    n = normalize_and_clean(desc)
    cls = json_data.get("clasificadores_legajo", []) or []
    matches = [c for c in cls if n in normalize_and_clean(str(c.get("clasificador", "")))]
    return {"clasificadores_por_descripcion": matches}

# ═══════════════════════════════════════════════════════════════
#  organismo_control
# ═══════════════════════════════════════════════════════════════

def obtener_organismo_control(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"organismo_control": json_data.get("organismo_control", {})}

def obtener_organismo_control_codigo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    oc = json_data.get("organismo_control", {}) or {}
    return {"organismo_control_codigo": oc.get("organismo_codigo")}

def obtener_organismo_control_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    oc = json_data.get("organismo_control", {}) or {}
    return {"organismo_control_descripcion": oc.get("organismo_descripcion")}

# ═══════════════════════════════════════════════════════════════
#  Campos raíz sueltos
# ═══════════════════════════════════════════════════════════════

def obtener_clave_causa(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"clave_causa": json_data.get("clave_causa")}

def obtener_codigo_sistema(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"codigo_sistema": json_data.get("codigo_sistema")}

def obtener_codigo_entidad(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"codigo_entidad": json_data.get("codigo_entidad")}

def obtener_estado_legajo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"estado": json_data.get("estado")}

def obtener_seguridad(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"seguridad": json_data.get("seguridad", [])}
