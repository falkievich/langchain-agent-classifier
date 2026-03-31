"""
extractors/causa.py
───────────────────
Funciones de extracción para "causa".
"""
from typing import Any, Dict

def _causa(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return json_data.get("causa", {}) or {}

# ═══════════════════════════════════════════════════════════════
#  Completa
# ═══════════════════════════════════════════════════════════════

def obtener_causa(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"causa": _causa(json_data)}

# ═══════════════════════════════════════════════════════════════
#  Campos individuales
# ═══════════════════════════════════════════════════════════════

def obtener_causa_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"causa_descripcion": _causa(json_data).get("descripcion")}

def obtener_causa_fecha_hecho(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"causa_fecha_hecho": _causa(json_data).get("fecha_hecho")}

def obtener_causa_forma_inicio(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"causa_forma_inicio": _causa(json_data).get("forma_inicio")}

def obtener_causa_nivel_acceso(json_data: Dict[str, Any]) -> Dict[str, Any]:
    c = _causa(json_data)
    return {
        "causa_nivel_acceso_descripcion": c.get("nivel_acceso_descripcion"),
    }

def obtener_causa_caratula_publica(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"causa_caratula_publica": _causa(json_data).get("caratula_publica")}

def obtener_causa_caratula_privada(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"causa_caratula_privada": _causa(json_data).get("caratula_privada")}
