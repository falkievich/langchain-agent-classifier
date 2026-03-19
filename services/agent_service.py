"""
services/agent_service.py
─────────────────────────
Servicio principal del agente.
Pipeline: LLM Planner → Query Executor (determinístico) → Resultado JSON.
"""
from typing import Any, Dict
from tools.pipeline import run_pipeline


async def generate_agent_response(user_prompt: str, json_data: Dict[str, Any]) -> str:
    """
    Pipeline principal.

    El LLM genera el plan (qué funciones semánticas, con qué filtros).
    La ejecución sobre el JSON es siempre determinística.
    Si el LLM falla → fallback al router por keywords.
    """
    try:
        return await run_pipeline(user_prompt, json_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


# Aliases para compatibilidad
generate_hybrid_response = generate_agent_response
generate_smart_response = generate_agent_response
