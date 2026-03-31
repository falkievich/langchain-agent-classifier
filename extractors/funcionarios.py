"""
extractors/funcionarios.py
──────────────────────────
Funciones de extracción para "funcionarios" y sus sub-nodos:
  - domicilios
"""
from typing import Any, Dict, List
from funcs.helpers_and_utility.langchain_utility import (
    buscar_entradas_en_lista,
    normalize_and_clean,
)

def _funcionarios(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return json_data.get("funcionarios", []) or []

# ═══════════════════════════════════════════════════════════════
#  Nivel 0: lista completa
# ═══════════════════════════════════════════════════════════════

def listar_funcionarios(json_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"funcionarios": _funcionarios(json_data)}

# ═══════════════════════════════════════════════════════════════
#  Nivel 1: búsqueda por campos directos
# ═══════════════════════════════════════════════════════════════

def buscar_funcionario_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "funcionarios",
                                       ["nombre_completo"], nombre, exact=False)
    return {"funcionarios_por_nombre": matches}

def buscar_funcionario_por_dni(json_data: Dict[str, Any], dni: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "funcionarios",
                                       ["numero_documento"], dni, exact=True)
    return {"funcionarios_por_dni": matches}

def buscar_funcionario_por_cuil(json_data: Dict[str, Any], cuil: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "funcionarios",
                                       ["cuil"], cuil, exact=True)
    return {"funcionarios_por_cuil": matches}

def buscar_funcionario_por_cargo(json_data: Dict[str, Any], cargo: str) -> Dict[str, Any]:
    n = normalize_and_clean(cargo)
    matches = [f for f in _funcionarios(json_data)
               if n in normalize_and_clean(str(f.get("cargo", "")))]
    return {"funcionarios_por_cargo": matches}

def buscar_funcionario_por_fecha_desde(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "funcionarios",
                                       ["fecha_desde"], fecha, exact=False)
    return {"funcionarios_por_fecha_desde": matches}

def buscar_funcionario_por_fecha_hasta(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "funcionarios",
                                       ["fecha_hasta"], fecha, exact=False)
    return {"funcionarios_por_fecha_hasta": matches}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: domicilios
# ═══════════════════════════════════════════════════════════════

def listar_domicilios_funcionarios(json_data: Dict[str, Any]) -> Dict[str, Any]:
    out = []
    for f in _funcionarios(json_data):
        doms = f.get("domicilios", []) or []
        if doms:
            out.append({
                "nombre_completo": f.get("nombre_completo"),
                "domicilios": doms,
            })
    return {"domicilios_funcionarios": out}

def buscar_domicilio_funcionario_por_email(json_data: Dict[str, Any], email: str) -> Dict[str, Any]:
    n = normalize_and_clean(email)
    out = []
    for f in _funcionarios(json_data):
        for dom in (f.get("domicilios") or []):
            if n in normalize_and_clean(str(dom.get("email", ""))):
                out.append({
                    "nombre_completo": f.get("nombre_completo"),
                    "domicilio": dom,
                })
    return {"domicilios_funcionario_por_email": out}
