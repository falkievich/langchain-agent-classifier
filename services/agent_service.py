from typing import Any, Dict
from classes.custom_llm_classes import CustomOpenWebLLM
from funcs.langchain.pipeline import run_pipeline


def get_llm() -> CustomOpenWebLLM:
    return CustomOpenWebLLM()


async def generate_agent_response(user_prompt: str, json_data: Dict[str, Any]) -> str:
    """
    Orquesta el flujo Intérprete → Normalizer → Searcher y devuelve JSON.
    Reutilizable por cualquier endpoint que tenga (user_prompt, json_data).

    Flujo:
      1. Intérprete (LLM): recibe pregunta, devuelve Plan validado por Pydantic
      2. Normalizer (código): traduce conceptos semánticos a valores reales del JSON
      3. Searcher (código): ejecuta el Plan sobre el JSON, devuelve resultado
    """
    try:
        llm = get_llm()
        result = await run_pipeline(llm, user_prompt, json_data)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
