"""
tools/query_executor.py
───────────────────────
Ejecutor determinístico de consultas semánticas.

Recibe un Plan (steps con función + filtros) y ejecuta sobre el JSON:
1. Lee el dominio del JSON correspondiente a la función.
2. Aplica los filtros (soporte para campos anidados y listas).
3. Extrae solo los paths definidos en FUNCTION_PATHS.
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


def _matches_all_filters(record: Dict[str, Any], filters: List[StepFilter]) -> bool:
    """Verifica que un registro pase TODOS los filtros (AND lógico)."""
    return all(_apply_filter(record, f) for f in filters)


# ═══════════════════════════════════════════════════════════════
#  Extracción de campos
# ═══════════════════════════════════════════════════════════════

def _extract_fields(record: Dict[str, Any], paths: List[str]) -> Dict[str, Any]:
    """
    Extrae solo los campos indicados de un registro.
    Los paths son de primer nivel (el sub-objeto completo se incluye).
    """
    result = {}
    for path in paths:
        top_key = path.split(".")[0]
        if top_key in record and top_key not in result:
            result[top_key] = record[top_key]
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
    paths = get_function_paths(func_name)

    # Obtener datos del dominio
    if domain == "_root":
        # Dominio especial: campos de la raíz del JSON
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
            "paths_used": [f"{domain}.{p}" for p in paths] if domain != "_root" else paths,
            "records": [],
            "record_count": 0,
        }

    # ── Dominio escalar (dict, no lista) ──
    if is_scalar:
        if isinstance(raw_data, dict):
            record = _extract_fields(raw_data, paths)
            # Aplicar filtros (raro en escalares, pero soportado)
            if step.filters and not _matches_all_filters(raw_data, step.filters):
                records = []
            else:
                records = [record]
        else:
            records = []

        return {
            "status": "ok",
            "function": func_name,
            "domain": domain,
            "filters_applied": [{"field": f.field, "op": f.op, "value": f.value} for f in step.filters],
            "paths_used": [f"{domain}.{p}" for p in paths] if domain != "_root" else paths,
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
        collection = [rec for rec in collection if _matches_all_filters(rec, step.filters)]

    # Extraer solo los paths definidos
    records = [_extract_fields(rec, paths) for rec in collection]

    return {
        "status": "ok",
        "function": func_name,
        "domain": domain,
        "filters_applied": [{"field": f.field, "op": f.op, "value": f.value} for f in step.filters],
        "paths_used": [f"{domain}.{p}" for p in paths] if domain != "_root" else paths,
        "records": records,
        "record_count": len(records),
    }


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
            "total_records": 5
        }
    """
    step_results: Dict[int, List[Dict[str, Any]]] = {}
    output_steps = []
    all_paths: List[str] = []
    total_records = 0

    for step in plan.steps:
        result = _execute_step(step, json_data, step_results)

        # Guardar registros para depends_on
        step_results[step.step_id] = result.get("records", [])

        # Acumular paths
        all_paths.extend(result.get("paths_used", []))
        total_records += result.get("record_count", 0)

        output_steps.append({
            "step_id": step.step_id,
            **result,
        })

    # Deduplica paths
    unique_paths = list(dict.fromkeys(all_paths))

    return {
        "steps": output_steps,
        "total_paths_used": unique_paths,
        "total_records": total_records,
    }
