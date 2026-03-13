"""
tools/pipeline.py
─────────────────
Pipeline único:

  LLM Planner (genera steps) → Executor Secuencial (determinístico) → JSON

  El LLM SIEMPRE genera el plan de ejecución:
    - Qué tools usar
    - En qué orden
    - Qué dependencias hay entre steps

  La ejecución es SIEMPRE determinística:
    - Las tools son funciones puras sobre el JSON
    - El encadenamiento de resultados es lógica fija en el executor

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

    1. LLM Planner genera steps secuenciales con dependencias.
    2. Executor ejecuta determinísticamente.
    3. Si el LLM falla → fallback al router por keywords.

    Returns:
        JSON string con bundle + metadata del plan generado.
    """
    # 1. LLM genera el plan
    plan = generate_plan_with_llm(user_prompt)

    # 2. Fallback si el LLM no devolvió steps válidos
    if not plan.steps:
        plan = route_query(user_prompt)
        plan_type = "fallback_deterministic"
    else:
        plan_type = "llm_sequential"

    # 3. Ejecutar
    bundle = await execute_plan(plan, json_data)

    # 4. Resultado con metadata del plan
    result: Dict[str, Any] = {
        "bundle": bundle,
        "plan_type": plan_type,
    }
    if plan.steps:
        result["plan"] = [
            {
                "step_id": s.step_id,
                "tool": s.tool,
                "args": s.args,
                "depends_on": s.depends_on,
                "output_field": s.output_field,
            }
            for s in plan.steps
        ]

    return json.dumps(result, ensure_ascii=False, indent=2)


# ── Alias para compatibilidad con código existente ──────────────
run_deterministic_pipeline = run_pipeline
run_hybrid_pipeline = run_pipeline
run_smart_pipeline = run_pipeline

