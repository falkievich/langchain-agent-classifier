"""
tools/executor.py
─────────────────
Ejecutor que soporta dos modos:

1. Ejecución PARALELA de Calls (para planes determinísticos simples).
2. Ejecución SECUENCIAL de Steps con dependencias (para planes del LLM).

En el modo secuencial, el resultado de un step puede filtrar el json_data
que recibe el siguiente step, permitiendo encadenar:
  buscar_persona_por_rol("victima") → listar_domicilios_personas (solo de víctimas)
"""
import asyncio
import copy
import json
from typing import Any, Dict, List, Tuple

from schema.call_and_plan_schema import Plan, Step
from extractors.registry import TOOL_BY_NAME
from funcs.helpers_and_utility.langchain_utility import normalize_and_clean

# ═══════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════

MAX_CONCURRENCY = 8
CALL_TIMEOUT_SEC = 10

_sem = asyncio.Semaphore(MAX_CONCURRENCY)


# ═══════════════════════════════════════════════════════════════
#  Ejecución de una sola tool
# ═══════════════════════════════════════════════════════════════

async def _execute_one(tool_name: str, json_data: Dict[str, Any],
                       args: List[Any]) -> Dict[str, Any]:
    """Ejecuta una sola tool de forma segura."""
    entry = TOOL_BY_NAME.get(tool_name)
    if not entry:
        return {"status": "error", "error": f"Tool '{tool_name}' no encontrada en el registro."}

    async with _sem:
        try:
            if entry.args == 0:
                result = await asyncio.wait_for(
                    asyncio.to_thread(entry.func, json_data),
                    timeout=CALL_TIMEOUT_SEC,
                )
            elif entry.args == 1 and len(args) >= 1:
                result = await asyncio.wait_for(
                    asyncio.to_thread(entry.func, json_data, args[0]),
                    timeout=CALL_TIMEOUT_SEC,
                )
            else:
                return {
                    "status": "error",
                    "error": f"Tool '{tool_name}' requiere {entry.args} argumento(s), se recibieron {len(args)}.",
                }
            return {"status": "ok", "data": result}
        except asyncio.TimeoutError:
            return {"status": "error", "error": f"Timeout ejecutando '{tool_name}'."}
        except Exception as e:
            return {"status": "error", "error": f"{type(e).__name__}: {e}"}


# ═══════════════════════════════════════════════════════════════
#  Ejecución PARALELA de Calls (modo determinístico simple)
# ═══════════════════════════════════════════════════════════════

async def execute_plan(plan: Plan, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ejecuta un plan. Si tiene steps, usa ejecución secuencial.
    Si tiene calls, usa ejecución paralela.
    """
    if plan.steps:
        return await _execute_steps(plan.steps, json_data)
    else:
        return await _execute_calls_parallel(plan, json_data)


async def _execute_calls_parallel(plan: Plan, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Ejecuta todas las calls del Plan en paralelo."""
    tasks = []
    for call in plan.calls:
        tasks.append(_execute_one(call.tool, json_data, call.args))

    results = await asyncio.gather(*tasks)

    bundle = []
    for call, result in zip(plan.calls, results):
        bundle.append({
            "tool": call.tool,
            "args": call.args,
            "result": result,
        })

    return bundle


# ═══════════════════════════════════════════════════════════════
#  Ejecución SECUENCIAL de Steps (modo con dependencias)
# ═══════════════════════════════════════════════════════════════

def _extract_names_from_result(result_data: Any) -> List[str]:
    """
    Extrae los nombre_completo de un resultado para usar como filtro.
    Busca recursivamente en dicts y listas.
    """
    names = []
    if isinstance(result_data, dict):
        # Buscar directamente en el dict
        if "nombre_completo" in result_data:
            names.append(result_data["nombre_completo"])
        # Buscar en los valores del dict
        for v in result_data.values():
            names.extend(_extract_names_from_result(v))
    elif isinstance(result_data, list):
        for item in result_data:
            names.extend(_extract_names_from_result(item))
    return names


def _extract_ids_from_result(result_data: Any, id_field: str = "persona_id") -> List[str]:
    """Extrae IDs de un resultado para usar como filtro."""
    ids = []
    if isinstance(result_data, dict):
        if id_field in result_data:
            ids.append(str(result_data[id_field]))
        for v in result_data.values():
            ids.extend(_extract_ids_from_result(v, id_field))
    elif isinstance(result_data, list):
        for item in result_data:
            ids.extend(_extract_ids_from_result(item, id_field))
    return ids


def _filter_json_by_names(json_data: Dict[str, Any], names: List[str], section: str) -> Dict[str, Any]:
    """
    Crea una copia del json_data donde la sección indicada solo contiene
    las entradas cuyos nombres coinciden con la lista.
    """
    if not names:
        return json_data

    filtered = copy.deepcopy(json_data)
    names_norm = {normalize_and_clean(n) for n in names if n}

    section_data = filtered.get(section, [])
    if isinstance(section_data, list):
        filtered_list = []
        for item in section_data:
            # Verificar por nombre_completo, nombre, apellido
            item_names = set()
            for field in ["nombre_completo", "nombre", "apellido"]:
                val = item.get(field)
                if val:
                    item_names.add(normalize_and_clean(val))

            if item_names & names_norm:
                filtered_list.append(item)

        filtered[section] = filtered_list

    return filtered


def _determine_section_for_tool(tool_name: str) -> str:
    """Determina la sección del JSON que usa una tool."""
    entry = TOOL_BY_NAME.get(tool_name)
    if entry:
        section_map = {
            "personas_legajo": "personas_legajo",
            "abogados_legajo": "abogados_legajo",
            "funcionarios": "funcionarios",
            "causa": "causa",
            "dependencias_vistas": "dependencias_vistas",
            "radicaciones": "radicaciones",
            "materia_delitos": "materia_delitos",
            "cabecera_legajo": "cabecera_legajo",
            "extras": "extras",
        }
        return section_map.get(entry.section, "personas_legajo")
    return "personas_legajo"


def _extract_output_field(result_data: Any, output_field: str) -> Any:
    """
    Extrae un sub-campo específico del resultado.
    Ej: output_field="domicilios" → extrae solo los domicilios de cada persona.
    """
    if not output_field:
        return result_data

    if isinstance(result_data, dict):
        # Buscar el campo directamente
        if output_field in result_data:
            return result_data[output_field]

        # Buscar en las listas dentro del dict
        extracted = {}
        for key, value in result_data.items():
            if isinstance(value, list):
                items_with_field = []
                for item in value:
                    if isinstance(item, dict):
                        # Incluir nombre para identificación + el campo solicitado
                        entry = {}
                        for id_f in ["nombre_completo", "nombre", "apellido",
                                     "abogado_nombre", "persona_nombre"]:
                            if id_f in item:
                                entry[id_f] = item[id_f]
                        if output_field in item:
                            entry[output_field] = item[output_field]
                            items_with_field.append(entry)
                if items_with_field:
                    extracted[key] = items_with_field
            elif isinstance(value, dict) and output_field in value:
                extracted[key] = value[output_field]

        return extracted if extracted else result_data

    return result_data


async def _execute_steps(steps: List[Step], json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ejecuta steps secuencialmente, encadenando resultados.
    
    Para cada step con depends_on:
    1. Extrae nombres del resultado del paso anterior
    2. Filtra el json_data para que solo contenga esas entidades
    3. Ejecuta la tool con el json_data filtrado
    4. Si hay output_field, extrae solo ese sub-campo
    """
    step_results: Dict[int, Dict[str, Any]] = {}  # step_id → result
    bundle = []

    for step in steps:
        # Determinar qué json_data usar
        current_json = json_data

        if step.depends_on is not None and step.depends_on in step_results:
            # Obtener resultado del paso anterior
            prev_result = step_results[step.depends_on]
            prev_data = prev_result.get("data", {})

            # Extraer nombres de las entidades del resultado anterior
            names = _extract_names_from_result(prev_data)

            if names:
                # Filtrar el json_data para que solo contenga esas entidades
                section = _determine_section_for_tool(step.tool)
                current_json = _filter_json_by_names(json_data, names, section)

        # Ejecutar la tool
        result = await _execute_one(step.tool, current_json, step.args)

        # Si hay output_field y el resultado es OK, extraer sub-campo
        if step.output_field and result.get("status") == "ok":
            result["data"] = _extract_output_field(result["data"], step.output_field)

        # Guardar resultado
        step_results[step.step_id] = result

        bundle.append({
            "step_id": step.step_id,
            "tool": step.tool,
            "args": step.args,
            "depends_on": step.depends_on,
            "output_field": step.output_field,
            "result": result,
        })

    return bundle
