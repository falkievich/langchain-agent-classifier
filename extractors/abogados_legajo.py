"""
extractors/abogados_legajo.py
─────────────────────────────
Funciones de extracción para "abogados_legajo" y sus sub-nodos:
  - representados
  - representados.domicilios
  - domicilios (nivel abogado)
"""
from typing import Any, Dict, List
from funcs.helpers_and_utility.langchain_utility import (
    buscar_entradas_en_lista,
    normalize_and_clean,
)

# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════

def _abogados(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return json_data.get("abogados_legajo", []) or []

# ═══════════════════════════════════════════════════════════════
#  Nivel 0: lista completa
# ═══════════════════════════════════════════════════════════════

def listar_abogados(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve todos los abogados del legajo."""
    return {"abogados_legajo": _abogados(json_data)}

# ═══════════════════════════════════════════════════════════════
#  Nivel 1: búsqueda por campos directos
# ═══════════════════════════════════════════════════════════════

def buscar_abogado_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["nombre", "apellido", "nombre_completo"],
                                       nombre, exact=True)
    return {"abogados_por_nombre": matches}

def buscar_abogado_por_dni(json_data: Dict[str, Any], dni: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["numero_documento"], dni, exact=True)
    return {"abogados_por_dni": matches}

def buscar_abogado_por_cuil(json_data: Dict[str, Any], cuil: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["cuil"], cuil, exact=True)
    return {"abogados_por_cuil": matches}

def buscar_abogado_por_matricula(json_data: Dict[str, Any], matricula: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["matricula"], matricula, exact=False)
    return {"abogados_por_matricula": matches}

def buscar_abogado_por_vinculo_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    """Filtra por vinculo_codigo (DPUB, DPRIV, etc.)."""
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["vinculo_codigo"], codigo, exact=True)
    return {"abogados_por_vinculo_codigo": matches}

def buscar_abogado_por_vinculo_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    """Filtra por vinculo_descripcion (defensor publico, defensor privado, etc.)."""
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["vinculo_descripcion"], desc, exact=False)
    return {"abogados_por_vinculo_descripcion": matches}

def buscar_abogado_por_fecha_nacimiento(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["fecha_nacimiento"], fecha, exact=False)
    return {"abogados_por_fecha_nacimiento": matches}

def buscar_abogado_por_fecha_desde(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["fecha_desde"], fecha, exact=False)
    return {"abogados_por_fecha_desde": matches}

def buscar_abogado_por_fecha_hasta(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "abogados_legajo",
                                       ["fecha_hasta"], fecha, exact=False)
    return {"abogados_por_fecha_hasta": matches}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: representados
# ═══════════════════════════════════════════════════════════════

def listar_representados(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve cada abogado con sus representados."""
    out = []
    for a in _abogados(json_data):
        rep = a.get("representados")
        if rep:
            # representados puede ser dict o lista
            reps = [rep] if isinstance(rep, dict) else (rep or [])
            out.append({
                "abogado_nombre": a.get("nombre_completo"),
                "representados": reps,
            })
    return {"representados_abogados": out}

def buscar_representado_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    """Busca representados por nombre_completo."""
    n = normalize_and_clean(nombre)
    out = []
    for a in _abogados(json_data):
        rep = a.get("representados")
        reps = [rep] if isinstance(rep, dict) else (rep or [])
        for r in reps:
            if n in normalize_and_clean(str(r.get("nombre_completo", ""))):
                out.append({
                    "abogado_nombre": a.get("nombre_completo"),
                    "representado": r,
                })
    return {"representados_por_nombre": out}

def buscar_representado_por_rol(json_data: Dict[str, Any], rol: str) -> Dict[str, Any]:
    """Busca representados por rol."""
    n = normalize_and_clean(rol)
    out = []
    for a in _abogados(json_data):
        rep = a.get("representados")
        reps = [rep] if isinstance(rep, dict) else (rep or [])
        for r in reps:
            roles = r.get("rol", [])
            if isinstance(roles, str):
                roles = [roles]
            for role in roles:
                if n in normalize_and_clean(str(role)):
                    out.append({
                        "abogado_nombre": a.get("nombre_completo"),
                        "representado": r,
                    })
                    break
    return {"representados_por_rol": out}

def buscar_abogados_de_cliente(json_data: Dict[str, Any], nombre_cliente: str) -> Dict[str, Any]:
    """Dado el nombre de un cliente/representado, devuelve los abogados que lo representan."""
    n = normalize_and_clean(nombre_cliente)
    out = []
    for a in _abogados(json_data):
        rep = a.get("representados")
        reps = [rep] if isinstance(rep, dict) else (rep or [])
        for r in reps:
            if n in normalize_and_clean(str(r.get("nombre_completo", ""))):
                out.append(a)
                break
    return {"abogados_de_cliente": out}

# ═══════════════════════════════════════════════════════════════
#  Nivel 3 – Sub-nodo: representados.domicilios
# ═══════════════════════════════════════════════════════════════

def listar_domicilios_representados(json_data: Dict[str, Any]) -> Dict[str, Any]:
    out = []
    for a in _abogados(json_data):
        rep = a.get("representados")
        reps = [rep] if isinstance(rep, dict) else (rep or [])
        for r in reps:
            doms = r.get("domicilios", []) or []
            if doms:
                out.append({
                    "abogado_nombre": a.get("nombre_completo"),
                    "representado_nombre": r.get("nombre_completo"),
                    "domicilios": doms,
                })
    return {"domicilios_representados": out}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: domicilios (del abogado directamente)
# ═══════════════════════════════════════════════════════════════

def listar_domicilios_abogados(json_data: Dict[str, Any]) -> Dict[str, Any]:
    out = []
    for a in _abogados(json_data):
        doms = a.get("domicilios", []) or []
        if doms:
            out.append({
                "nombre_completo": a.get("nombre_completo"),
                "domicilios": doms,
            })
    return {"domicilios_abogados": out}

def buscar_domicilio_abogado_por_clase(json_data: Dict[str, Any], clase: str) -> Dict[str, Any]:
    n = normalize_and_clean(clase)
    out = []
    for a in _abogados(json_data):
        for dom in (a.get("domicilios") or []):
            if n in normalize_and_clean(str(dom.get("clase", ""))):
                out.append({
                    "nombre_completo": a.get("nombre_completo"),
                    "domicilio": dom,
                })
    return {"domicilios_abogado_por_clase": out}

def buscar_domicilio_abogado_por_tipo(json_data: Dict[str, Any], tipo: str) -> Dict[str, Any]:
    """
    Busca domicilios de abogado buscando el argumento en TODOS los campos del
    objeto domicilio (clase, digital_clase, digital_clase_codigo, empresa,
    empresa_codigo, relacion_vinculo, descripcion, etc.).
    De esta forma cubre cualquier campo sin importar cuál sea.
    Ejemplos de uso: "celular", "CEL", "ELECTRONICO", "PROPIO", "Sin especificar".
    """
    n = normalize_and_clean(tipo)
    out = []
    for a in _abogados(json_data):
        for dom in (a.get("domicilios") or []):
            valores = [
                normalize_and_clean(str(v))
                for v in dom.values()
                if v is not None and not isinstance(v, (dict, list))
            ]
            if any(n in v for v in valores):
                out.append({
                    "nombre_completo": a.get("nombre_completo"),
                    "domicilio": dom,
                })
    return {"domicilios_abogado_por_tipo": out}
