from typing import Any, Dict, List, Callable

# Importamos los registros de funciones por dominio
from langchain_tools.abogado_tool import ALL_ABOGADO_FUNCS
from langchain_tools.expediente_tool import ALL_EXPEDIENTES_FUNCS
from langchain_tools.persona_legajo_tool import ALL_PERSONAS_FUNCS
from langchain_tools.dependencias_vistas_tool import ALL_DEPENDENCIAS_FUNCS
from langchain_tools.materia_delitos_tool import ALL_MATERIA_DELITOS_FUNCS
from langchain_tools.radicacion_tool import ALL_RADICACIONES_FUNCS
from langchain_tools.arrays_tool import ALL_ARRAYS_FUNCS


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


# ====================== GLOBAL SEARCHES ======================

def buscar_por_codigo_global(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    """
    Busca un código en cualquier dominio (abogados, dependencias, radicaciones, etc.).
    Internamente prueba múltiples funciones hasta encontrar un match.
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


def buscar_por_nombre_global(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    """
    Busca por nombre en diferentes dominios (abogados, funcionarios, personas).
    """
    attempts = [
        "buscar_abogado_por_nombre",
        "buscar_funcionario_por_nombre",
        "buscar_persona_por_nombre",
    ]
    return _first_success_by_names_arg(json_data, nombre, attempts)


def buscar_por_fecha_global(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    """
    Busca por fecha en distintos dominios (personas, radicaciones, dependencias, abogados).
    """
    attempts = [
        "buscar_persona_por_fecha_participacion",
        "buscar_persona_por_fecha_vinculo",
        "buscar_persona_por_fecha_nacimiento",
        "buscar_radicacion_por_fecha",
        "buscar_dependencias_por_fecha",
        "buscar_representados_por_fecha_representacion",
    ]
    return _first_success_by_names_arg(json_data, fecha, attempts)
