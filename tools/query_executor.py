"""
tools/query_executor.py
───────────────────────
Ejecutor determinístico de consultas semánticas.

Recibe un Plan (steps con función + filtros + output_paths) y ejecuta sobre el JSON:
1. Lee el dominio del JSON correspondiente a la función.
2. Aplica los filtros (soporte para campos anidados y listas).
3. Extrae los paths indicados en step.output_paths (si los hay) o todos los de FUNCTION_PATHS.
4. Encadena resultados entre steps (depends_on).

El LLM nunca toca este código. Solo genera el plan.
"""
import copy
from typing import Any, Dict, List, Optional, Set

from schema.call_and_plan_schema import Plan, Step, StepFilter
from schema.function_catalog import (
    FUNCTION_CATALOG,
    FUNCTION_PATHS,
    get_function_domain,
    is_scalar_domain,
    get_function_paths,
)
from funcs.helpers_and_utility.langchain_utility import normalize_and_clean


# ═══════════════════════════════════════════════════════════════
#  Acceso a campos anidados
# ═══════════════════════════════════════════════════════════════

def _get_nested(obj: Any, path: str) -> Any:
    """
    Accede a un path con notación punto sobre dicts y listas.
    Ej: 'vinculos.descripcion_vinculo' sobre una persona que tiene vinculos=[{...}]
    Devuelve un valor escalar o una lista aplanada de valores.
    """
    parts = path.split(".")
    return _resolve_path(obj, parts)


def _resolve_path(obj: Any, parts: List[str]) -> Any:
    """Resolución recursiva de path."""
    if not parts:
        return obj
    if obj is None:
        return None

    key = parts[0]
    rest = parts[1:]

    if isinstance(obj, dict):
        child = obj.get(key)
        if child is None:
            return None
        return _resolve_path(child, rest)

    elif isinstance(obj, list):
        # Si es una lista, resolver sobre cada elemento y aplanar
        results = []
        for item in obj:
            val = _resolve_path(item, [key] + rest) if isinstance(item, dict) else None
            if val is not None:
                if isinstance(val, list):
                    results.extend(val)
                else:
                    results.append(val)
        return results if results else None

    return None


# ═══════════════════════════════════════════════════════════════
#  Filtrado
# ═══════════════════════════════════════════════════════════════

def _apply_filter(record: Dict[str, Any], filt: StepFilter) -> bool:
    """
    Aplica un filtro a un registro.
    Soporta campos anidados (ej: vinculos.descripcion_vinculo).
    Si el campo resuelve a una lista, basta que UN elemento cumpla.
    """
    raw = _get_nested(record, filt.field)
    if raw is None:
        return False

    # Normalizar a lista para evaluación uniforme
    values = raw if isinstance(raw, list) else [raw]
    values = [normalize_and_clean(str(v)) for v in values if v is not None]

    target = normalize_and_clean(filt.value)

    if filt.op == "eq":
        return any(v == target for v in values)
    elif filt.op == "contains":
        return any(target in v for v in values)
    elif filt.op == "gte":
        return any(v >= target for v in values if v)
    elif filt.op == "lte":
        return any(v <= target for v in values if v)
    return False


def _matches_filters(record: Dict[str, Any], filters: List[StepFilter], filter_op: str = "AND") -> bool:
    """
    Verifica que un registro pase los filtros según el operador lógico indicado.
      AND → todos los filtros deben cumplirse.
      OR  → al menos uno debe cumplirse.
    """
    if not filters:
        return True
    if filter_op == "OR":
        return any(_apply_filter(record, f) for f in filters)
    return all(_apply_filter(record, f) for f in filters)


def _matches_same_entity(record: Dict[str, Any], filters: List[StepFilter], filter_op: str = "AND") -> bool:
    """
    Versión SAME_ENTITY: todos los filtros deben cumplirse sobre el MISMO
    sub-elemento de una lista anidada (ej: mismo objeto de 'vinculos').

    Algoritmo:
      1. Detecta el top-level key de los filtros que tienen path anidado
         (ej: "vinculos.descripcion_vinculo" → top = "vinculos").
      2. Para cada elemento de esa lista, verifica si el sub-elemento
         satisface TODOS los filtros contra él.
      3. Los filtros de campos planos (sin lista) se evalúan normalmente.

    Si no hay paths anidados con listas → delega a _matches_filters normal.
    """
    if not filters:
        return True

    # Separar filtros planos de filtros anidados
    nested_filters: Dict[str, List[StepFilter]] = {}   # top_key → [filters]
    flat_filters: List[StepFilter] = []

    for f in filters:
        parts = f.field.split(".", 1)
        if len(parts) == 2:
            top_key = parts[0]
            val = record.get(top_key)
            if isinstance(val, list):
                nested_filters.setdefault(top_key, []).append(f)
                continue
        flat_filters.append(f)

    # Si no hay filtros anidados sobre listas → comportamiento normal
    if not nested_filters:
        return _matches_filters(record, filters, filter_op)

    # Evaluar filtros planos primero
    if flat_filters and not _matches_filters(record, flat_filters, filter_op):
        return False

    # Para cada grupo de filtros anidados, buscar UN elemento de la lista
    # que satisfaga TODOS los filtros de ese grupo (la misma entidad)
    for top_key, grp_filters in nested_filters.items():
        sub_list = record.get(top_key, []) or []
        if not isinstance(sub_list, list):
            return False

        # Crear filtros "relativos" al sub-elemento (quitar el prefijo top_key)
        relative_filters = []
        for f in grp_filters:
            _, sub_path = f.field.split(".", 1)
            relative_filters.append(StepFilter(field=sub_path, op=f.op, value=f.value))

        # Verificar que ALGÚN elemento de la lista satisfaga TODOS los filtros relativos
        found = any(
            _matches_filters(item, relative_filters, "AND")
            for item in sub_list
            if isinstance(item, dict)
        )
        if not found:
            return False

    return True


# Alias para compatibilidad con código existente
def _matches_all_filters(record: Dict[str, Any], filters: List[StepFilter]) -> bool:
    """Alias legacy: AND sobre todos los filtros."""
    return _matches_filters(record, filters, "AND")


# ═══════════════════════════════════════════════════════════════
#  Extracción de campos
# ═══════════════════════════════════════════════════════════════

def _extract_fields(record: Dict[str, Any], paths: List[str]) -> Dict[str, Any]:
    """
    Extrae los campos indicados de un registro.

    Soporta dos modos según el formato del path:
      - Path de primer nivel ("nombre_completo", "vinculos"):
        copia la clave completa tal cual está en el registro.
      - Path anidado ("domicilios.domicilio.provincia"):
        proyecta solo los sub-campos indicados dentro del objeto/lista,
        reconstruyendo la estructura mínima necesaria.

    Esto permite devolver, por ejemplo, solo province+ciudad dentro de
    cada elemento de la lista domicilios, sin traer todos los campos.
    """
    # Agrupar paths por su top-level key
    top_level_only: List[str] = []          # paths sin punto → copia directa
    nested_by_top: Dict[str, List[str]] = {}  # "domicilios" → ["domicilio.provincia", ...]

    for path in paths:
        parts = path.split(".", 1)
        if len(parts) == 1:
            top_level_only.append(parts[0])
        else:
            top_key, sub_path = parts
            nested_by_top.setdefault(top_key, []).append(sub_path)

    result: Dict[str, Any] = {}

    # 1. Paths de primer nivel: copia directa
    for key in top_level_only:
        if key in record and key not in result:
            result[key] = record[key]

    # 2. Paths anidados: proyección mínima
    for top_key, sub_paths in nested_by_top.items():
        if top_key not in record:
            continue
        value = record[top_key]

        if isinstance(value, list):
            # Proyectar cada elemento de la lista
            projected_list = []
            for item in value:
                if isinstance(item, dict):
                    projected_list.append(_project_nested(item, sub_paths))
                else:
                    projected_list.append(item)
            result[top_key] = projected_list

        elif isinstance(value, dict):
            result[top_key] = _project_nested(value, sub_paths)

        else:
            # Valor escalar: se incluye directamente
            result[top_key] = value

    return result


def _project_nested(obj: Dict[str, Any], sub_paths: List[str]) -> Dict[str, Any]:
    """
    Proyecta sub_paths sobre un dict, recursivamente.
    sub_paths son paths relativos al dict (ej: ["domicilio.provincia", "tipo"]).
    """
    result: Dict[str, Any] = {}
    for sub_path in sub_paths:
        parts = sub_path.split(".", 1)
        key = parts[0]
        if key not in obj:
            continue
        if len(parts) == 1:
            # Leaf: incluir directamente
            if key not in result:
                result[key] = obj[key]
        else:
            # Recursivo
            child = obj[key]
            rest = parts[1]
            if isinstance(child, dict):
                sub_result = _project_nested(child, [rest])
                existing = result.get(key, {})
                if isinstance(existing, dict):
                    existing.update(sub_result)
                    result[key] = existing
                else:
                    result[key] = sub_result
            elif isinstance(child, list):
                projected = [_project_nested(c, [rest]) if isinstance(c, dict) else c for c in child]
                result[key] = projected
            else:
                result[key] = child
    return result


# ═══════════════════════════════════════════════════════════════
#  Cruce entre steps (depends_on)
# ═══════════════════════════════════════════════════════════════

def _extract_identity_keys(records: List[Dict[str, Any]]) -> Set[str]:
    """
    Extrae claves de identidad de los registros del step padre
    para cruzar con el step hijo.
    Busca: persona_id, nombre_completo, numero_documento, abogado_id.
    También busca en sub-listas como 'relacionados' y 'representados'.
    """
    keys = set()
    for rec in records:
        for field in ("persona_id", "abogado_id", "funcionario_id",
                      "nombre_completo", "numero_documento"):
            val = rec.get(field)
            if val:
                keys.add(normalize_and_clean(str(val)))

        # Extraer IDs de relacionados (abogados embebidos en personas)
        for sub_field in ("relacionados", "representados"):
            sub_list = rec.get(sub_field, []) or []
            if isinstance(sub_list, list):
                for sub in sub_list:
                    if isinstance(sub, dict):
                        for f in ("persona_id", "abogado_persona_id",
                                  "nombre_completo", "numero_documento"):
                            v = sub.get(f)
                            if v:
                                keys.add(normalize_and_clean(str(v)))
    return keys


def _filter_by_parent(
    collection: List[Dict[str, Any]],
    parent_keys: Set[str],
) -> List[Dict[str, Any]]:
    """
    Filtra una colección para solo incluir registros cuya identidad
    esté en las claves del step padre.
    """
    if not parent_keys:
        return collection

    filtered = []
    for record in collection:
        matched = False
        for field in ("persona_id", "abogado_id", "abogado_persona_id",
                      "funcionario_id", "nombre_completo", "numero_documento"):
            val = record.get(field)
            if val and normalize_and_clean(str(val)) in parent_keys:
                matched = True
                break

        # Cruce inverso: representados → personas
        if not matched:
            for sub_field in ("representados", "relacionados"):
                sub_list = record.get(sub_field, []) or []
                if isinstance(sub_list, list):
                    for sub in sub_list:
                        if isinstance(sub, dict):
                            for f in ("persona_id", "nombre_completo", "numero_documento"):
                                v = sub.get(f)
                                if v and normalize_and_clean(str(v)) in parent_keys:
                                    matched = True
                                    break
                        if matched:
                            break
                if matched:
                    break

        if matched:
            filtered.append(record)

    return filtered if filtered else collection


# ═══════════════════════════════════════════════════════════════
#  Ejecución de un step
# ═══════════════════════════════════════════════════════════════

def _execute_step(
    step: Step,
    json_data: Dict[str, Any],
    previous_results: Dict[int, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Ejecuta un step del plan.

    Selección de paths:
      - Si step.output_paths está definido → usa esos paths (pedidos por el LLM).
      - Si no                              → fallback a FUNCTION_PATHS completos.

    Returns:
        {
            "status": "ok" | "error",
            "function": nombre de la función,
            "domain": dominio del JSON,
            "filters_applied": [...],
            "paths_used": [...],
            "records": [...],
            "record_count": int,
            "error": str (solo si error)
        }
    """
    func_name = step.function
    meta = FUNCTION_CATALOG.get(func_name)

    if not meta:
        return {
            "status": "error",
            "function": func_name,
            "error": f"Función '{func_name}' no encontrada en el catálogo.",
        }

    domain = meta["domain"]
    is_scalar = meta.get("is_scalar", False)

    # ── Resolución de paths ──────────────────────────────────────
    # Si el LLM pidió paths específicos, usarlos; si no, usar todos los de FUNCTION_PATHS.
    if step.output_paths:
        paths = step.output_paths
        # Siempre garantizar el ID de identidad para encadenamiento (depends_on)
        _ensure_identity_path(paths, func_name, domain)
    else:
        paths = get_function_paths(func_name)
    # ────────────────────────────────────────────────────────────

    # Prefijo para paths_used en la respuesta
    def _prefixed(p: str) -> str:
        if domain == "_root" or p.startswith(domain + ".") or "." in p:
            return f"{domain}.{p}" if domain != "_root" and not p.startswith(domain) else p
        return f"{domain}.{p}"

    def _build_paths_used(output_paths: List[str]) -> List[str]:
        """
        Construye la lista completa de paths usados:
          1. Paths de filtros aplicados  →  "domain.field = value"
          2. Paths de salida             →  "domain.field"
        Sin duplicados, manteniendo el orden filtros → salida.
        """
        seen: set = set()
        result: List[str] = []

        # 1. Filtros aplicados
        for f in step.filters:
            entry = f"{_prefixed(f.field)} = {f.value}"
            if entry not in seen:
                seen.add(entry)
                result.append(entry)

        # 2. Paths de salida
        for p in output_paths:
            entry = _prefixed(p)
            if entry not in seen:
                seen.add(entry)
                result.append(entry)

        return result

    # Obtener datos del dominio
    if domain == "_root":
        raw_data = json_data
        is_scalar = True
    else:
        raw_data = json_data.get(domain)

    if raw_data is None:
        return {
            "status": "ok",
            "function": func_name,
            "domain": domain,
            "filters_applied": [f.__dict__ for f in step.filters],
            "paths_used": _build_paths_used(paths),
            "records": [],
            "record_count": 0,
        }

    # ── Dominio escalar (dict, no lista) ──
    if is_scalar:
        if isinstance(raw_data, dict):
            record = _extract_fields(raw_data, paths)
            if step.filters:
                match = _matches_filters(raw_data, step.filters, getattr(step, "filter_op", "AND"))
                if getattr(step, "negate", False):
                    match = not match
                records = [] if not match else [record]
            else:
                records = [record]
        else:
            records = []

        return {
            "status": "ok",
            "function": func_name,
            "domain": domain,
            "filters_applied": [{"field": f.field, "op": f.op, "value": f.value} for f in step.filters],
            "paths_used": _build_paths_used(paths),
            "records": records,
            "record_count": len(records),
        }

    # ── Dominio de colección (lista) ──
    if not isinstance(raw_data, list):
        raw_data = [raw_data] if isinstance(raw_data, dict) else []

    collection = raw_data

    # Aplicar depends_on: filtrar por resultados del step padre
    if step.depends_on is not None and step.depends_on in previous_results:
        parent_records = previous_results[step.depends_on]
        parent_keys = _extract_identity_keys(parent_records)
        collection = _filter_by_parent(collection, parent_keys)

    # Aplicar filtros propios
    if step.filters:
        filter_op   = getattr(step, "filter_op",   "AND")
        negate      = getattr(step, "negate",      False)
        same_entity = getattr(step, "same_entity", False)

        def _record_matches(rec: Dict[str, Any]) -> bool:
            if same_entity:
                match = _matches_same_entity(rec, step.filters, filter_op)
            else:
                match = _matches_filters(rec, step.filters, filter_op)
            return (not match) if negate else match

        collection = [rec for rec in collection if _record_matches(rec)]

    # Extraer campos
    records = [_extract_fields(rec, paths) for rec in collection]

    return {
        "status": "ok",
        "function": func_name,
        "domain": domain,
        "filters_applied": [{"field": f.field, "op": f.op, "value": f.value} for f in step.filters],
        "paths_used": _build_paths_used(paths),
        "records": records,
        "record_count": len(records),
    }


# ── IDs de identidad garantizados por dominio ────────────────────
_IDENTITY_FIELDS: Dict[str, str] = {
    "personas_legajo": "persona_id",
    "abogados_legajo": "abogado_id",
    "funcionarios":    "funcionario_id",
}

def _ensure_identity_path(paths: List[str], func_name: str, domain: str) -> None:
    """
    Asegura que el campo de identidad (persona_id, etc.) esté en paths
    para que el encadenamiento depends_on funcione correctamente.
    Modifica la lista in-place.
    """
    id_field = _IDENTITY_FIELDS.get(domain)
    if id_field and id_field not in paths:
        paths.insert(0, id_field)


# ═══════════════════════════════════════════════════════════════
#  Ejecución del plan completo
# ═══════════════════════════════════════════════════════════════

def execute_plan(plan: Plan, json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ejecuta el plan completo generado por el LLM.

    Returns:
        {
            "steps": [
                {
                    "step_id": 1,
                    "function": "get_personas",
                    "domain": "personas_legajo",
                    "filters_applied": [...],
                    "paths_used": [...],
                    "records": [...],
                    "record_count": 3
                },
                ...
            ],
            "total_paths_used": ["personas_legajo.nombre", ...],
            "query_string": "(campo1=valor1 AND campo2=valor2) AND campo3=valor3",
            "total_records": 5
        }
    """
    step_results: Dict[int, List[Dict[str, Any]]] = {}
    output_steps = []
    all_paths: List[str] = []
    total_records = 0
    # Acumula los filtros de cada step en orden, para query_string agrupada
    steps_filters: List[List[Dict[str, Any]]] = []

    for step in plan.steps:
        result = _execute_step(step, json_data, step_results)

        # Guardar registros para depends_on
        step_results[step.step_id] = result.get("records", [])

        # Acumular paths (para total_paths_used)
        all_paths.extend(result.get("paths_used", []))
        total_records += result.get("record_count", 0)

        # Acumular filtros agrupados por step (para query_string)
        steps_filters.append({
            "filters":     result.get("filters_applied", []),
            "domain":      result.get("domain", ""),
            "filter_op":   getattr(step, "filter_op",   "AND"),
            "negate":      getattr(step, "negate",      False),
            "same_entity": getattr(step, "same_entity", False),
        })

        output_steps.append({
            "step_id": step.step_id,
            **result,
        })

    # Deduplica paths manteniendo orden
    unique_paths = list(dict.fromkeys(all_paths))

    return {
        "steps": output_steps,
        "total_paths_used": unique_paths,
        "query_string": _build_query_string(steps_filters),
        "total_records": total_records,
    }


def _build_query_string(steps_filters: List[Dict[str, Any]]) -> str:
    """
    Construye la query string agrupando los filtros por step.

    Cada filtro se prefija con el dominio del step:
      personas_legajo.vinculos.descripcion_vinculo contains imputado

    Modificadores por step:
      - filter_op   = AND | OR  → une las condiciones dentro del grupo
      - negate      = True      → envuelve el grupo con NOT(...)
      - same_entity = True      → envuelve el grupo con SAME_ENTITY(...)

    Los grupos se unen entre sí siempre con AND.
    Se deduplicán filtros sueltos idénticos que aparezcan en múltiples steps.
    Los grupos compuestos (SAME_ENTITY, NOT, OR, multi-filtro) nunca se deduplicán
    entre sí porque su semántica depende del contexto completo del grupo.
    """
    def _fmt(f: Dict[str, Any], domain: str) -> str:
        raw_field = f.get("field", "")
        op        = f.get("op", "eq")
        value     = f.get("value", "")

        # Prefijar con dominio si no es _root y el field no lo tiene ya
        if domain and domain != "_root" and not raw_field.startswith(domain + "."):
            field = f"{domain}.{raw_field}"
        else:
            field = raw_field

        if op == "eq":
            return f"{field}={value}"
        elif op == "contains":
            return f"{field} contains {value}"
        elif op == "gte":
            return f"{field}>={value}"
        elif op == "lte":
            return f"{field}<={value}"
        elif op == "neq":
            return f"{field}!={value}"
        return f"{field}={value}"

    groups: List[str] = []
    seen_simple: set = set()   # ← track de filtros sueltos ya emitidos

    for step in steps_filters:
        filters     = step.get("filters",     [])
        domain      = step.get("domain",      "")
        filter_op   = step.get("filter_op",   "AND")
        negate      = step.get("negate",      False)
        same_entity = step.get("same_entity", False)

        if not filters:
            continue

        is_compound = same_entity or negate or filter_op == "OR" or len(filters) > 1

        if is_compound:
            # ── Grupo compuesto: deduplicar filtros DENTRO del grupo ──
            parts: List[str] = []
            seen_in_group: set = set()
            for f in filters:
                part = _fmt(f, domain)
                if part not in seen_in_group:
                    seen_in_group.add(part)
                    parts.append(part)

            if not parts:
                continue

            sep   = f" {filter_op} "
            inner = sep.join(parts)

            if same_entity:
                group = f"SAME_ENTITY({inner})"
            else:
                group = f"({inner})" if len(parts) > 1 else inner

            if negate:
                group = f"NOT {group}"

            groups.append(group)
        else:
            # ── Filtro suelto: deduplicar entre steps ──
            part = _fmt(filters[0], domain)
            if part not in seen_simple:
                seen_simple.add(part)
                groups.append(part)

    return " AND ".join(groups)
