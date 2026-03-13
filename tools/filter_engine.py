"""
tools/filter_engine.py
──────────────────────
Motor de filtrado post-ejecución.

Aplica los ConditionFilter extraídos por el LLM sobre los resultados
devueltos por las funciones extractoras.

Es puramente determinístico: recibe datos + filtros y devuelve datos filtrados.
"""
import re
from typing import Any, Dict, List, Optional
from funcs.helpers_and_utility.langchain_utility import normalize_and_clean
from tools.condition_extractor import ConditionFilter


# ═══════════════════════════════════════════════════════════════
#  Operadores de comparación
# ═══════════════════════════════════════════════════════════════

def _normalize(val: Any) -> str:
    """Normaliza un valor para comparación."""
    if val is None:
        return ""
    return normalize_and_clean(str(val))


def _to_number(val: str) -> Optional[float]:
    """Intenta convertir a número."""
    try:
        return float(val.replace(",", "."))
    except (ValueError, TypeError):
        return None


def _apply_operator(actual_value: Any, operator: str, filter_value: str) -> bool:
    """Aplica un operador de comparación entre valor real y valor de filtro."""
    actual_norm = _normalize(actual_value)
    filter_norm = _normalize(filter_value)

    if operator == "eq":
        return actual_norm == filter_norm

    elif operator == "ne":
        return actual_norm != filter_norm

    elif operator == "contains":
        return filter_norm in actual_norm

    elif operator == "exists":
        target = filter_norm in ("true", "si", "1", "yes")
        has_value = actual_value is not None and str(actual_value).strip() != ""
        return has_value == target

    elif operator in ("gt", "lt", "gte", "lte"):
        a = _to_number(actual_norm)
        b = _to_number(filter_norm)
        if a is not None and b is not None:
            if operator == "gt":  return a > b
            if operator == "lt":  return a < b
            if operator == "gte": return a >= b
            if operator == "lte": return a <= b
        # Fallback: comparación lexicográfica
        if operator == "gt":  return actual_norm > filter_norm
        if operator == "lt":  return actual_norm < filter_norm
        if operator == "gte": return actual_norm >= filter_norm
        if operator == "lte": return actual_norm <= filter_norm

    # Operador desconocido → no filtrar
    return True


# ═══════════════════════════════════════════════════════════════
#  Resolución de campo en un objeto anidado
# ═══════════════════════════════════════════════════════════════

def _resolve_field(obj: Dict[str, Any], field: str) -> Any:
    """
    Resuelve un campo en un objeto JSON, soportando:
    - Campos directos: "nombre", "genero"
    - Campos anidados con punto: "vinculos.codigo", "caracteristicas.genero"
    - Campos dentro de arrays: busca en sub-arrays
    """
    parts = field.split(".")

    current = obj
    for i, part in enumerate(parts):
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                # Intentar búsqueda case-insensitive
                found = False
                for key in current:
                    if _normalize(key) == _normalize(part):
                        current = current[key]
                        found = True
                        break
                if not found:
                    return None
        elif isinstance(current, list):
            # Buscar en cada elemento del array
            remaining = ".".join(parts[i:])
            results = []
            for item in current:
                if isinstance(item, dict):
                    val = _resolve_field(item, remaining)
                    if val is not None:
                        results.append(val)
            return results if results else None
        else:
            return None

    return current


# ═══════════════════════════════════════════════════════════════
#  Campos alternativos / aliases
# ═══════════════════════════════════════════════════════════════

# Mapea campos del filtro a posibles campos reales en el JSON
FIELD_ALIASES: Dict[str, List[str]] = {
    "rol":                      ["vinculos.descripcion", "vinculos.codigo", "vinculo_descripcion", "vinculo_codigo"],
    "vinculo_descripcion":      ["vinculos.descripcion", "vinculo_descripcion"],
    "vinculo_codigo":           ["vinculos.codigo", "vinculo_codigo"],
    "genero":                   ["caracteristicas.genero", "genero"],
    "es_menor":                 ["caracteristicas.esMenor", "es_menor"],
    "estado_detencion":         ["detencion", "estado_detencion", "estaDetenido"],
    "ocupacion":                ["caracteristicas.ocupacion", "ocupacion"],
    "estado_civil":             ["caracteristicas.estadoCivil", "estado_civil"],
    "nivel_educativo":          ["caracteristicas.nivelEducativo", "nivel_educativo"],
    "lugar_nacimiento":         ["caracteristicas.lugarNacimiento", "lugar_nacimiento"],
    "cargo":                    ["cargo", "cargo_descripcion"],
    "nombre":                   ["nombre_completo", "nombre", "apellido"],
    "matricula":                ["matricula", "numero_matricula"],
    "activo":                   ["activo", "esActivo"],
}


def _resolve_with_aliases(obj: Dict[str, Any], field: str) -> Any:
    """Resuelve un campo usando aliases si el campo directo no existe."""
    # Intentar campo directo primero
    val = _resolve_field(obj, field)
    if val is not None:
        return val

    # Buscar en aliases
    aliases = FIELD_ALIASES.get(field, [])
    for alias in aliases:
        val = _resolve_field(obj, alias)
        if val is not None:
            return val

    return None


# ═══════════════════════════════════════════════════════════════
#  Filtrado de un solo registro
# ═══════════════════════════════════════════════════════════════

def _record_matches_filter(record: Dict[str, Any], f: ConditionFilter) -> bool:
    """Verifica si un registro cumple con un filtro."""
    actual = _resolve_with_aliases(record, f.field)

    if actual is None:
        # Si el campo no existe, no matchea (a menos que op sea "exists" con false)
        return f.operator == "exists" and _normalize(f.value) in ("false", "no", "0")

    # Si el valor resuelto es una lista (de sub-arrays), verificar si alguno matchea
    if isinstance(actual, list):
        return any(_apply_operator(v, f.operator, f.value) for v in actual)

    return _apply_operator(actual, f.operator, f.value)


def _record_matches_all_filters(record: Dict[str, Any], filters: List[ConditionFilter]) -> bool:
    """Verifica si un registro cumple TODOS los filtros (AND lógico)."""
    return all(_record_matches_filter(record, f) for f in filters)


# ═══════════════════════════════════════════════════════════════
#  API principal: filtrar bundle de resultados
# ═══════════════════════════════════════════════════════════════

def apply_filters_to_bundle(
    bundle: List[Dict[str, Any]],
    filters: List[ConditionFilter],
    data_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Aplica filtros al bundle de resultados del executor.
    
    Cada item del bundle tiene: {tool, args, result: {status, data}}
    
    - Si result.data contiene una lista, filtra los items de la lista.
    - Si result.data es un dict con una key que contiene una lista, filtra esa lista.
    - Si data_fields no es None y no es ["*"], extrae solo esos campos.
    
    Returns: bundle filtrado.
    """
    if not filters and (not data_fields or data_fields == ["*"]):
        return bundle  # nada que filtrar

    filtered_bundle = []
    for item in bundle:
        result = item.get("result", {})
        if result.get("status") != "ok":
            filtered_bundle.append(item)  # mantener errores sin filtrar
            continue

        data = result.get("data", {})
        filtered_data = _apply_filters_to_data(data, filters, data_fields)

        filtered_bundle.append({
            "tool": item["tool"],
            "args": item["args"],
            "result": {"status": "ok", "data": filtered_data},
        })

    return filtered_bundle


def _apply_filters_to_data(
    data: Any,
    filters: List[ConditionFilter],
    data_fields: Optional[List[str]] = None,
) -> Any:
    """Aplica filtros a un resultado de datos genérico."""

    # Si data es una lista directamente
    if isinstance(data, list):
        filtered = [r for r in data if _record_matches_all_filters(r, filters)] if filters else data
        if data_fields and data_fields != ["*"]:
            filtered = [_project_fields(r, data_fields) for r in filtered]
        return filtered

    # Si data es un dict con una clave principal que contiene una lista
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, list):
                # Aplicar filtros a la lista
                filtered_list = [r for r in value if _record_matches_all_filters(r, filters)] if filters else value
                if data_fields and data_fields != ["*"]:
                    filtered_list = [_project_fields(r, data_fields) for r in filtered_list]
                result[key] = filtered_list
            else:
                result[key] = value
        return result

    # Si data es un valor primitivo, no filtrar
    return data


def _project_fields(record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """
    Proyecta solo los campos especificados de un registro.
    Si un campo no existe, se omite.
    Si fields contiene "*", devuelve todo.
    """
    if "*" in fields or not fields:
        return record

    projected = {}
    for f in fields:
        val = _resolve_with_aliases(record, f)
        if val is not None:
            projected[f] = val
        else:
            # Intentar búsqueda parcial en keys
            for key in record:
                if _normalize(f) in _normalize(key):
                    projected[key] = record[key]

    # Si no se encontró nada, devolver el registro completo
    # (mejor tener datos de más que de menos)
    if not projected:
        return record

    # Siempre incluir campos de identificación
    for id_field in ["nombre_completo", "nombre", "apellido", "ide", "clave"]:
        if id_field in record and id_field not in projected:
            projected[id_field] = record[id_field]

    return projected
