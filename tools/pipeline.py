"""
tools/pipeline.py
─────────────────
Pipeline único:

  LLM Planner (genera steps semánticos) → Query Executor (determinístico) → JSON

  El LLM SIEMPRE genera el plan de ejecución:
    - Qué funciones semánticas usar
    - Con qué filtros
    - En qué orden y con qué dependencias

  La ejecución es SIEMPRE determinística:
    - Las funciones son mapeos de paths sobre el JSON
    - Los filtros son comparaciones sobre campos
    - El encadenamiento de resultados es lógica fija en el query_executor

  Fallback:
    - Si el LLM falla o devuelve un plan inválido → router por keywords
"""
import json
from typing import Any, Dict

from tools.llm_planner import generate_plan_with_llm
from tools.deterministic_router import route_query
from tools.executor import execute_plan


async def run_pipeline(
    user_prompt: str,
    json_data: Dict[str, Any],
) -> str:
    """
    Pipeline principal. El LLM siempre genera el plan.

    1. LLM Planner genera steps con funciones semánticas + filtros.
    2. Query Executor ejecuta determinísticamente sobre el JSON.
    3. Si el LLM falla → fallback al router por keywords.

    Returns:
        JSON string con resultados + metadata del plan generado.
    """
    # 1. LLM genera el plan
    plan = generate_plan_with_llm(user_prompt)

    # 2. Fallback si el LLM no devolvió steps válidos
    if not plan.steps:
        plan = route_query(user_prompt)
        plan_type = "fallback_deterministic"
    else:
        plan_type = "llm_semantic"

    # 3. Ejecutar
    result = await execute_plan(plan, json_data)

    # 4. Resultado con metadata del plan
    output: Dict[str, Any] = {
        "plan_type": plan_type,
        "plan": [
            {
                "step_id": s.step_id,
                "function": s.function,
                "filters": [
                    {"field": f.field, "op": f.op, "value": f.value}
                    for f in s.filters
                ],
                "depends_on": s.depends_on,
            }
            for s in plan.steps
        ],
        **result,  # steps, total_paths_used, total_records
    }

    return json.dumps(output, ensure_ascii=False, indent=2)


# ── Alias para compatibilidad con código existente ──────────────
run_deterministic_pipeline = run_pipeline
run_hybrid_pipeline = run_pipeline
run_smart_pipeline = run_pipeline

