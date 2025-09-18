import json
from pydantic import ValidationError

# -------- Importaciones --------
# CustomOpenWebLLM: wrapper del LLM para invocar el modelo.
from classes.custom_llm_classes import CustomOpenWebLLM

# Plan: esquema Pydantic que define el contrato del Planner (lista de calls).
from schema.call_and_plan_schema import Plan

# PLANNER_SYSTEM_TPL / PLANNER_USER_TMPL: prompts del Planner (system + user).
# MAX_CALLS: límite de cantidad de llamadas permitidas en el plan.
from funcs.langchain.core import PLANNER_SYSTEM_TPL, PLANNER_USER_TMPL, MAX_CALLS


# -------- Planner --------
# Esta sección construye el "plan" de ejecución:
# - Formatea el listado de tools para el prompt.
# - Llama al LLM con un system + user que exigen JSON estricto.
# - Recorta defensivamente el JSON, lo valida con Pydantic y aplica reglas:
#   * Tools válidas (presentes en allowed_tools)
#   * Límite de llamadas (MAX_CALLS)
# Devuelve un objeto Plan listo para ser ejecutado en paralelo.

def build_tools_bullets(allowed_tools) -> str:
    """Convierte la lista de tools en bullets para el prompt del Planner."""
    return "\n".join(f"- {t.name}: {t.description}" for t in allowed_tools)

def run_planner(llm: CustomOpenWebLLM, user_prompt: str, allowed_tools, max_calls: int = MAX_CALLS) -> Plan:
    """Invoca al Planner (LLM) para obtener un plan JSON y lo valida."""

    # 1) Preparar prompts (system + user) con reglas y listado de tools
    system = PLANNER_SYSTEM_TPL.substitute(max_calls=max_calls)
    tools_bullets = build_tools_bullets(allowed_tools)
    user = PLANNER_USER_TMPL.format(user_prompt=user_prompt, tools_bullets=tools_bullets)

    # 2) Llamar al LLM (una sola vez) para que devuelva SOLO JSON
    raw = llm._call(prompt=f"{system}\n\n{user}", stop=None)

    # 3) Recortar defensivamente, por si viene texto extra antes/después del JSON
    json_str = raw.strip()
    if not json_str.startswith("{"):
        start, end = json_str.find("{"), json_str.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = json_str[start:end+1]

    # 4) Parsear + validar contra el esquema Plan
    try:
        data = json.loads(json_str)
        plan = Plan(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise RuntimeError(f"Planner devolvió JSON inválido: {e}\nRAW:\n{raw}")

    # 5) Validaciones de negocio (tools permitidas + tope de llamadas)
    allowed_names = {t.name for t in allowed_tools}
    for c in plan.calls:
        if c.tool not in allowed_names:
            raise RuntimeError(f"Tool no permitida en plan: {c.tool}")

    if len(plan.calls) > max_calls:
        plan.calls = plan.calls[:max_calls]

    return plan

# -------- Registry --------
# Esta sección crea el "registry" (diccionario) que mapea nombre de tool → callable:
# - Soporta tools con .func (callable Python)
# - Soporta Runnables con .invoke (se envuelven como función)
# El registry es lo que usa el ejecutor para disparar cada call del plan.


def build_registry(tools):
    """Construye {nombre_tool: callable} desde la lista de tools de LangChain."""
    registry = {}
    for t in tools:
        if hasattr(t, "func") and callable(getattr(t, "func")):
            registry[t.name] = t.func
        elif hasattr(t, "invoke") and callable(getattr(t, "invoke")):
            # Envolvemos el Runnable para poder llamarlo como función normal
            def make_invoke(tt):
                def _call(*args, **kwargs):
                    return tt.invoke(*args, **kwargs)
                return _call
            registry[t.name] = make_invoke(t)
        else:
            raise RuntimeError(f"No sé cómo ejecutar la tool: {t.name}")
    return registry
