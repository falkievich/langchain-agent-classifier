from typing import Any, Dict, List
from classes.custom_llm_classes import CustomOpenWebLLM
from funcs.langchain.pipeline import run_planned_parallel

# Importamos las Tools
from wrappers.listados_wrappers import make_listados_tools
from wrappers.domain_search_wrappers import make_domain_search_tools
from wrappers.global_search_wrappers import make_global_search_tools


def build_all_tools(json_data: Dict[str, Any]) -> List[Any]:
    """Crea y devuelve la lista completa de tools a partir del json_data."""
    tools = (
        make_listados_tools(json_data)
        + make_domain_search_tools(json_data)
        + make_global_search_tools(json_data)
    )

    # Print esencial: mostrar tools disponibles
    # print("\n=== TOOLS DISPONIBLES PARA EL LLM ===")
    # for t in tools:
    #     try:
    #         print(f"- {t.name}: {t.description}")
    #     except Exception:
    #         print(f"- {t}")
    # print("======================================\n")

    return tools


def get_llm() -> CustomOpenWebLLM:
    return CustomOpenWebLLM()

async def generate_agent_response(user_prompt: str, json_data: Dict[str, Any]) -> str:
    """
    Orquesta el flujo Planner → Parallel → Finalizer y devuelve texto final.
    Reutilizable por cualquier endpoint que tenga (user_prompt, json_data).
    """
    try:
        tools = build_all_tools(json_data)
        llm = get_llm()
        result = await run_planned_parallel(llm, user_prompt, tools)
        return result
    except Exception as e:
        # print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise
