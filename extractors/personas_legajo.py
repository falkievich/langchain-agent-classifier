"""
extractors/personas_legajo.py
─────────────────────────────
Funciones de extracción para "personas_legajo" y sus sub-nodos:
  - vinculos
  - caracteristicas
  - calificaciones_legales
  - relacionados  (persona / abogado)
  - relacionados.domicilios
  - domicilios (nivel persona)
"""
from typing import Any, Dict, List
from funcs.helpers_and_utility.langchain_utility import (
    buscar_entradas_en_lista,
    normalize_and_clean,
    _to_bool_flag,
)

# ═══════════════════════════════════════════════════════════════
#  Helpers internos
# ═══════════════════════════════════════════════════════════════

def _personas(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return json_data.get("personas_legajo", []) or []

def _filtrar(personas: list, campo: str, valor: str, exact: bool = True) -> list:
    """Filtro genérico sobre lista de personas por campo de primer nivel."""
    n = normalize_and_clean(valor)
    out = []
    for p in personas:
        v = normalize_and_clean(str(p.get(campo, "")))
        if (exact and v == n) or (not exact and n in v):
            out.append(p)
    return out

# ═══════════════════════════════════════════════════════════════
#  Nivel 0: lista completa
# ═══════════════════════════════════════════════════════════════

def listar_personas(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve todas las personas del legajo."""
    return {"personas_legajo": _personas(json_data)}

# ═══════════════════════════════════════════════════════════════
#  Nivel 1: búsqueda por campos directos de persona
# ═══════════════════════════════════════════════════════════════

def buscar_persona_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    """Busca por nombre, apellido o nombre_completo."""
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["nombre", "apellido", "nombre_completo"],
                                       nombre, exact=True)
    return {"personas_por_nombre": matches}

def buscar_persona_por_dni(json_data: Dict[str, Any], numero_documento: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["numero_documento"], numero_documento, exact=True)
    return {"personas_por_dni": matches}

def buscar_persona_por_cuil(json_data: Dict[str, Any], cuil: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["cuil"], cuil, exact=True)
    return {"personas_por_cuil": matches}

def buscar_persona_por_tipo_documento(json_data: Dict[str, Any], tipo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["tipo_documento"], tipo, exact=False)
    return {"personas_por_tipo_documento": matches}

def buscar_persona_por_fecha_nacimiento(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["fecha_nacimiento"], fecha, exact=False)
    return {"personas_por_fecha_nacimiento": matches}

def buscar_persona_por_genero(json_data: Dict[str, Any], genero: str) -> Dict[str, Any]:
    matches = _filtrar(_personas(json_data), "genero", genero, exact=False)
    return {"personas_por_genero": matches}

def buscar_persona_por_rol(json_data: Dict[str, Any], rol: str) -> Dict[str, Any]:
    """Busca dentro del array 'rol' de cada persona."""
    n = normalize_and_clean(rol)
    out = []
    for p in _personas(json_data):
        roles = p.get("rol", []) or []
        if isinstance(roles, str):
            roles = [roles]
        for r in roles:
            if n in normalize_and_clean(str(r)):
                out.append(p)
                break
    return {"personas_por_rol": out}

def buscar_persona_por_estado_detencion(json_data: Dict[str, Any], flag: Any) -> Dict[str, Any]:
    b = _to_bool_flag(flag)
    matches = [p for p in _personas(json_data)
               if isinstance(p.get("es_detenido"), bool) and p["es_detenido"] == b]
    return {"personas_por_estado_detencion": matches}

def buscar_persona_por_fecha_desde(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["fecha_desde"], fecha, exact=False)
    return {"personas_por_fecha_desde": matches}

def buscar_persona_por_fecha_hasta(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["fecha_hasta"], fecha, exact=False)
    return {"personas_por_fecha_hasta": matches}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: vinculos
# ═══════════════════════════════════════════════════════════════

def listar_vinculos_personas(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve nombre_completo + vinculos de cada persona."""
    out = []
    for p in _personas(json_data):
        out.append({
            "nombre_completo": p.get("nombre_completo"),
            "vinculos": p.get("vinculos", []),
        })
    return {"vinculos_personas": out}

def buscar_persona_por_codigo_vinculo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["vinculos.codigo_vinculo"], codigo, exact=True)
    return {"personas_por_codigo_vinculo": matches}

def buscar_persona_por_descripcion_vinculo(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "personas_legajo",
                                       ["vinculos.descripcion_vinculo"], desc, exact=False)
    return {"personas_por_descripcion_vinculo": matches}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: caracteristicas
# ═══════════════════════════════════════════════════════════════

def listar_caracteristicas_personas(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve nombre_completo + caracteristicas de cada persona."""
    out = []
    for p in _personas(json_data):
        out.append({
            "nombre_completo": p.get("nombre_completo"),
            "caracteristicas": p.get("caracteristicas", []),
        })
    return {"caracteristicas_personas": out}

def buscar_persona_por_caracteristica_genero(json_data: Dict[str, Any], genero: str) -> Dict[str, Any]:
    """Busca dentro de caracteristicas[].genero."""
    n = normalize_and_clean(genero)
    out = []
    for p in _personas(json_data):
        for c in (p.get("caracteristicas") or []):
            if n in normalize_and_clean(str(c.get("genero", ""))):
                out.append(p)
                break
    return {"personas_por_caracteristica_genero": out}

def buscar_persona_por_es_menor(json_data: Dict[str, Any], flag: Any) -> Dict[str, Any]:
    b = _to_bool_flag(flag)
    out = []
    for p in _personas(json_data):
        for c in (p.get("caracteristicas") or []):
            if c.get("es_menor") == b:
                out.append(p)
                break
    return {"personas_por_es_menor": out}

def buscar_persona_por_ocupacion(json_data: Dict[str, Any], ocupacion: str) -> Dict[str, Any]:
    n = normalize_and_clean(ocupacion)
    out = []
    for p in _personas(json_data):
        for c in (p.get("caracteristicas") or []):
            if n in normalize_and_clean(str(c.get("ocupacion", ""))):
                out.append(p)
                break
    return {"personas_por_ocupacion": out}

def buscar_persona_por_estado_civil(json_data: Dict[str, Any], estado: str) -> Dict[str, Any]:
    n = normalize_and_clean(estado)
    out = []
    for p in _personas(json_data):
        for c in (p.get("caracteristicas") or []):
            if n in normalize_and_clean(str(c.get("estado_civil", ""))):
                out.append(p)
                break
    return {"personas_por_estado_civil": out}

def buscar_persona_por_nivel_educativo(json_data: Dict[str, Any], nivel: str) -> Dict[str, Any]:
    n = normalize_and_clean(nivel)
    out = []
    for p in _personas(json_data):
        for c in (p.get("caracteristicas") or []):
            if n in normalize_and_clean(str(c.get("nivel_educativo", ""))):
                out.append(p)
                break
    return {"personas_por_nivel_educativo": out}

def buscar_persona_por_lugar_nacimiento(json_data: Dict[str, Any], lugar: str) -> Dict[str, Any]:
    n = normalize_and_clean(lugar)
    out = []
    for p in _personas(json_data):
        for c in (p.get("caracteristicas") or []):
            if n in normalize_and_clean(str(c.get("lugar_nacimiento", ""))):
                out.append(p)
                break
    return {"personas_por_lugar_nacimiento": out}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: calificaciones_legales
# ═══════════════════════════════════════════════════════════════

def listar_calificaciones_legales_personas(json_data: Dict[str, Any]) -> Dict[str, Any]:
    out = []
    for p in _personas(json_data):
        cal = p.get("calificaciones_legales")
        if cal:
            out.append({
                "nombre_completo": p.get("nombre_completo"),
                "calificaciones_legales": cal,
            })
    return {"calificaciones_legales_personas": out}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: relacionados
# ═══════════════════════════════════════════════════════════════

def listar_relacionados_personas(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve nombre_completo de la persona + sus relacionados."""
    out = []
    for p in _personas(json_data):
        rels = p.get("relacionados", []) or []
        if rels:
            out.append({
                "nombre_completo": p.get("nombre_completo"),
                "relacionados": rels,
            })
    return {"relacionados_personas": out}

def buscar_relacionado_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    """Busca dentro de relacionados por nombre/apellido/nombre_completo."""
    n = normalize_and_clean(nombre)
    out = []
    for p in _personas(json_data):
        for rel in (p.get("relacionados") or []):
            for campo in ["nombre", "apellido", "nombre_completo"]:
                if n in normalize_and_clean(str(rel.get(campo, ""))):
                    out.append({
                        "persona_nombre": p.get("nombre_completo"),
                        "relacionado": rel,
                    })
                    break
    return {"relacionados_por_nombre": out}

def buscar_relacionado_por_tipo(json_data: Dict[str, Any], tipo: str) -> Dict[str, Any]:
    """Filtra relacionados por tipo (persona, abogado)."""
    n = normalize_and_clean(tipo)
    out = []
    for p in _personas(json_data):
        for rel in (p.get("relacionados") or []):
            if n in normalize_and_clean(str(rel.get("tipo", ""))):
                out.append({
                    "persona_nombre": p.get("nombre_completo"),
                    "relacionado": rel,
                })
    return {"relacionados_por_tipo": out}

def buscar_relacionado_por_rol(json_data: Dict[str, Any], rol: str) -> Dict[str, Any]:
    """Filtra relacionados por su campo 'rol'."""
    n = normalize_and_clean(rol)
    out = []
    for p in _personas(json_data):
        for rel in (p.get("relacionados") or []):
            if n in normalize_and_clean(str(rel.get("rol", ""))):
                out.append({
                    "persona_nombre": p.get("nombre_completo"),
                    "relacionado": rel,
                })
    return {"relacionados_por_rol": out}

# ═══════════════════════════════════════════════════════════════
#  Nivel 3 – Sub-nodo: relacionados.domicilios
# ═══════════════════════════════════════════════════════════════

def listar_domicilios_relacionados(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve los domicilios de todos los relacionados."""
    out = []
    for p in _personas(json_data):
        for rel in (p.get("relacionados") or []):
            doms = rel.get("domicilios", []) or []
            if doms:
                out.append({
                    "persona_nombre": p.get("nombre_completo"),
                    "relacionado_nombre": rel.get("nombre_completo") or rel.get("nombre"),
                    "domicilios": doms,
                })
    return {"domicilios_relacionados": out}

# ═══════════════════════════════════════════════════════════════
#  Nivel 2 – Sub-nodo: domicilios (de persona directamente)
# ═══════════════════════════════════════════════════════════════

def listar_domicilios_personas(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve los domicilios de cada persona."""
    out = []
    for p in _personas(json_data):
        doms = p.get("domicilios", []) or []
        if doms:
            out.append({
                "nombre_completo": p.get("nombre_completo"),
                "domicilios": doms,
            })
    return {"domicilios_personas": out}

def buscar_domicilio_persona_por_clase(json_data: Dict[str, Any], clase: str) -> Dict[str, Any]:
    """Filtra domicilios de persona por clase (FISICO, ELECTRONICO)."""
    n = normalize_and_clean(clase)
    out = []
    for p in _personas(json_data):
        for dom in (p.get("domicilios") or []):
            if n in normalize_and_clean(str(dom.get("clase", ""))):
                out.append({
                    "nombre_completo": p.get("nombre_completo"),
                    "domicilio": dom,
                })
    return {"domicilios_persona_por_clase": out}

def buscar_domicilio_persona_por_descripcion(json_data: Dict[str, Any], desc: str) -> Dict[str, Any]:
    """Busca en el campo 'descripcion' (teléfono, email, dirección, etc.)."""
    n = normalize_and_clean(desc)
    out = []
    for p in _personas(json_data):
        for dom in (p.get("domicilios") or []):
            if n in normalize_and_clean(str(dom.get("descripcion", ""))):
                out.append({
                    "nombre_completo": p.get("nombre_completo"),
                    "domicilio": dom,
                })
    return {"domicilios_persona_por_descripcion": out}

def buscar_domicilio_persona_por_relacion_vinculo(json_data: Dict[str, Any], relacion: str) -> Dict[str, Any]:
    """Filtra domicilios por relacion_vinculo (PROPIO, HERMANO, TIO, etc.)."""
    n = normalize_and_clean(relacion)
    out = []
    for p in _personas(json_data):
        for dom in (p.get("domicilios") or []):
            if n in normalize_and_clean(str(dom.get("relacion_vinculo", ""))):
                out.append({
                    "nombre_completo": p.get("nombre_completo"),
                    "domicilio": dom,
                })
    return {"domicilios_persona_por_relacion": out}
