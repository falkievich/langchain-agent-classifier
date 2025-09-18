from typing import Any, Dict, List
from classes.custom_llm_classes import CustomOpenWebLLM
from funcs.langchain.pipeline import run_planned_parallel # Importamos las Pipeline

# Tus factories para tools
from tools_wrappers.abogado_wrappers import make_abogado_tools
from tools_wrappers.expediente_wrappers import make_expediente_tools
from tools_wrappers.persona_legajo_wrappers import make_persona_legajo_tools
from tools_wrappers.dependencias_wrappers import make_dependencias_tools
from tools_wrappers.materia_delitos_wrappers import make_materia_delitos_tools
from tools_wrappers.radicacion_wrappers import make_radicacion_tools
from tools_wrappers.arrays_wrappers import make_arrays_tools

def build_all_tools(json_data: Dict[str, Any]) -> List[Any]:
    """Crea y devuelve la lista completa de tools a partir del json_data."""
    return (
        make_abogado_tools(json_data)
        + make_expediente_tools(json_data)
        + make_persona_legajo_tools(json_data)
        + make_dependencias_tools(json_data)
        + make_materia_delitos_tools(json_data)
        + make_radicacion_tools(json_data)
        + make_arrays_tools(json_data)
    )

def get_llm() -> CustomOpenWebLLM:
    return CustomOpenWebLLM()

async def generate_agent_response(user_prompt: str, json_data: Dict[str, Any]) -> str:
    """
    Orquesta el flujo Planner → Parallel → Finalizer y devuelve texto final.
    Reutilizable por cualquier endpoint que tenga (user_prompt, json_data).
    """
    tools = build_all_tools(json_data)
    llm = get_llm()
    return await run_planned_parallel(llm, user_prompt, tools)
