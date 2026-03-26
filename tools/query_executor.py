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


def _matches_all_filters(record: Dict[str, Any], filters: List[StepFilter]) -> bool:
    """Verifica que un registro pase TODOS los filtros (AND lógico)."""
    return all(_apply_filter(record, f) for f in filters)


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
        collection = [rec for rec in collection if _matches_all_filters(rec, step.filters)]

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
        "query_string": _build_query_string(unique_paths),
        "total_records": total_records,
    }


def _build_query_string(paths: List[str]) -> str:
    """
    Convierte total_paths_used al formato de query string de la API.

    Solo incluye paths que tienen valor (filtros aplicados):
      - "campo = valor"  → campo=valor

    Paths de salida sin valor se omiten (no son válidos en Postman).
    Múltiples valores para el mismo campo se unen con "," (OR implícito).
    Campos distintos se unen con "&" (AND implícito).

    Ejemplo de salida:
      personas_legajo.vinculos.descripcion_vinculo=victima&personas_legajo.caracteristicas.es_menor=true
    """
    from collections import OrderedDict

    filter_fields: "OrderedDict[str, List[str]]" = OrderedDict()

    for entry in paths:
        if " = " in entry:
            field, value = entry.split(" = ", 1)
            field, value = field.strip(), value.strip()
            if field not in filter_fields:
                filter_fields[field] = []
            if value not in filter_fields[field]:
                filter_fields[field].append(value)

    if not filter_fields:
        return ""

    return "&".join(
        f"{field}={','.join(values)}"
        for field, values in filter_fields.items()
    )
