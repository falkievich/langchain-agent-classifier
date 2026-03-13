from typing import Any, Dict
from tools.pipeline import run_pipeline


async def generate_agent_response(user_prompt: str, json_data: Dict[str, Any]) -> str:
    """
    Pipeline principal.

    El LLM siempre genera el plan (qué tools, qué orden, qué dependencias).
    La ejecución de las tools es siempre determinística.
    Si el LLM falla → fallback al router por keywords.
    """
    try:
        return await run_pipeline(user_prompt, json_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


# Aliases para no romper código existente que importe estas funciones
generate_hybrid_response = generate_agent_response
generate_smart_response = generate_agent_response
