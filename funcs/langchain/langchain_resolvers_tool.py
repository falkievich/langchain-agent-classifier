# Tools/resolvers_tool.py
from typing import Any, Dict, List, Callable

# ===== Importá SOLO las listas de funciones =====
from tools.abogado_tool import ALL_ABOGADO_FUNCS
from tools.expediente_tool import ALL_EXPEDIENTES_FUNCS
from tools.persona_legajo_tool import ALL_PERSONAS_FUNCS
from tools.dependencias_vistas_tool import ALL_DEPENDENCIAS_FUNCS
from tools.materia_delitos_tool import ALL_MATERIA_DELITOS_FUNCS
from tools.radicacion_tool import ALL_RADICACIONES_FUNCS
from tools.arrays_tool import ALL_ARRAYS_FUNCS

# ---------- Registry global: nombre → función ----------
_ALL_LISTS = (
    ALL_ABOGADO_FUNCS
    + ALL_EXPEDIENTES_FUNCS
    + ALL_PERSONAS_FUNCS
    + ALL_DEPENDENCIAS_FUNCS
    + ALL_MATERIA_DELITOS_FUNCS
    + ALL_RADICACIONES_FUNCS
    + ALL_ARRAYS_FUNCS
)
FUNC_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {f.__name__: f for f in _ALL_LISTS}

# ============ Helpers mínimos (secos, sin heurísticas) ============
def _has_payload(r: Any) -> bool:
    """True si es dict no vacío con algún valor truthy."""
    return isinstance(r, dict) and bool(r) and any(bool(v) for v in r.values())

def _first_success_by_names_arg(
    json_data: Dict[str, Any],
    arg: Any,
    fn_names: List[str],
) -> Dict[str, Any]:
    """Ejecuta funciones (json_data, arg) en orden; retorna primer match."""
    for name in fn_names:
        fn = FUNC_REGISTRY.get(name)
        if not fn:
            continue
        try:
            res = fn(json_data, arg)
            if _has_payload(res):
                return {"matched_via": name, "query": arg, "result": res}
        except Exception:
            pass
    return {}

def _first_success_by_names_noarg(
    json_data: Dict[str, Any],
    fn_names: List[str],
) -> Dict[str, Any]:
    """Ejecuta funciones (json_data) en orden; retorna primer match."""
    for name in fn_names:
        fn = FUNC_REGISTRY.get(name)
        if not fn:
            continue
        try:
            res = fn(json_data)
            if _has_payload(res):
                return {"matched_via": name, "result": res}
        except Exception:
            pass
    return {}

# ============ PATRONES AMBIGUOS (cuando el LLM no sabe el rol) ============

def resolver_por_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    """
    Identificador alfanumérico ambiguo entre dominios.
    Orden fijo, stop-on-first-match. (Tu lista de 'Código')
    """
    attempts = [
        "buscar_dependencias_por_organismo_codigo",
        "buscar_dependencias_por_codigo",
        "buscar_dependencias_por_clase_codigo",
        "buscar_persona_por_codigo_vinculo",
        "buscar_delito_por_codigo",
        "buscar_radicacion_por_organismo_codigo",
        "buscar_radicacion_por_motivo_codigo",
        "buscar_abogado_por_matricula",
    ]
    return _first_success_by_names_arg(json_data, codigo, attempts)

def resolver_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    """Nombre sin rol: abogado -> funcionario -> persona."""
    attempts = [
        "buscar_abogado_por_nombre",
        "buscar_funcionario_por_nombre",
        "buscar_persona_por_nombre",
    ]
    return _first_success_by_names_arg(json_data, nombre, attempts)

def resolver_por_descripcion(json_data: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
    """Descripción ambigua que puede mapear a varias áreas."""
    attempts = [
        "buscar_dependencias_por_organismo_descripcion",
        "buscar_dependencias_por_dependencia_descripcion",
        "buscar_dependencias_por_clase_descripcion",
        "buscar_delitos_por_descripcion",
        "buscar_radicacion_por_organismo_descripcion",
        "buscar_radicacion_por_motivo_descripcion",
        "buscar_causa_por_descripcion",
        "buscar_clasificacion_legajo_por_descripcion",
    ]
    return _first_success_by_names_arg(json_data, descripcion, attempts)

def resolver_por_rol(json_data: Dict[str, Any], rol: str) -> Dict[str, Any]:
    """‘Rol’ ambiguo: ¿persona o dependencia?"""
    attempts = [
        "buscar_persona_por_rol",
        "buscar_dependencias_por_rol",
    ]
    return _first_success_by_names_arg(json_data, rol, attempts)

def resolver_por_estado(json_data: Dict[str, Any], estado: str) -> Dict[str, Any]:
    """Estado/condición ambigua: persona.detención vs dependencia.activo."""
    attempts = [
        "buscar_persona_por_estado_detencion",
        "buscar_dependencias_por_activo",
    ]
    return _first_success_by_names_arg(json_data, estado, attempts)

# ============ RESOLVER POR ÁREA (cobertura amplia 1x1) ============

def resolver_por_persona(json_data: Dict[str, Any], query: str) -> Dict[str, Any]:
    attempts = [
        "buscar_persona_por_numero_documento_dni",
        "buscar_persona_por_numero_cuil",
        "buscar_persona_por_nombre",
        "buscar_persona_por_rol",
        "buscar_persona_por_descripcion_vinculo",
        "buscar_persona_por_tipo_documento",
        "buscar_persona_por_estado_detencion",
    ]
    return _first_success_by_names_arg(json_data, query, attempts)

def resolver_por_dependencia(json_data: Dict[str, Any], query: str) -> Dict[str, Any]:
    attempts = [
        "buscar_dependencias_por_organismo_codigo",
        "buscar_dependencias_por_codigo",
        "buscar_dependencias_por_clase_codigo",
        "buscar_dependencias_por_organismo_descripcion",
        "buscar_dependencias_por_dependencia_descripcion",
        "buscar_dependencias_por_clase_descripcion",
        "buscar_dependencias_por_rol",
        "buscar_dependencias_por_tipos",
        "buscar_dependencias_por_jerarquia",
        "buscar_dependencias_por_activo",
    ]
    return _first_success_by_names_arg(json_data, query, attempts)

def resolver_por_delito(json_data: Dict[str, Any], query: str) -> Dict[str, Any]:
    attempts = [
        "buscar_delito_por_codigo",
        "buscar_delito_por_orden",
        "buscar_delitos_por_descripcion",
    ]
    return _first_success_by_names_arg(json_data, query, attempts)

def resolver_por_radicacion(json_data: Dict[str, Any], query: str) -> Dict[str, Any]:
    attempts = [
        "buscar_radicacion_por_organismo_codigo",
        "buscar_radicacion_por_organismo_descripcion",
        "buscar_radicacion_por_motivo_codigo",
        "buscar_radicacion_por_motivo_descripcion",
        "buscar_radicacion_por_fecha",
    ]
    return _first_success_by_names_arg(json_data, query, attempts)

def resolver_por_expediente(json_data: Dict[str, Any], _prompt_o_vacio: str = "") -> Dict[str, Any]:
    attempts = [
        "buscar_estado_expediente",
        "buscar_materias_expediente",
        "buscar_fechas_clave",
        "obtener_info_general_expediente",
    ]
    return _first_success_by_names_noarg(json_data, attempts)

# ============ Export para ALL_FUNCS (para que el LLM pueda llamarlas) ============
# Patrones ambiguos (cuando NO está claro el rol/tipo)
RESOLVER_AMBIGUOS_FUNCS = [
    resolver_por_codigo,
    resolver_por_nombre,
    resolver_por_descripcion,
    resolver_por_rol,
    resolver_por_estado,
]

# Resolución por área (explora un dominio 1x1)
RESOLVER_AREA_FUNCS = [
    resolver_por_persona,
    resolver_por_dependencia,
    resolver_por_delito,
    resolver_por_radicacion,
    resolver_por_expediente,
]
