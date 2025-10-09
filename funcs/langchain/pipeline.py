from langchain_core.runnables import RunnableLambda
import json

# -------- Importaciones --------
from classes.custom_llm_classes import CustomOpenWebLLM # wrapper del LLM para invocar el modelo.
from funcs.langchain.planning import run_planner, build_registry # Importamos el Plan y el Registro
from funcs.langchain.execution import execute_plan_parallel, run_finalizer # Importamos la Ejecutor del Plan y el Finalizador
from funcs.langchain.core import MAX_CALLS # Límite de cantidad de llamadas permitidas en el plan.

# -------- Pipeline --------
# 1) prep_step: arma el contexto y el registry.
# 2) plan_step: obtiene el Plan (JSON) del Planner.
# 3) exec_step: ejecuta el Plan en paralelo y trae el bundle.
# 4) final_step: invoca el Finalizer y devuelve texto final.

# 1) Preparar contexto
prep_step = RunnableLambda(lambda x: {
    "llm": x["llm"],
    "user_prompt": x["user_prompt"],
    "tools": x["tools"],
    "registry": build_registry(x["tools"]),
})

# 2) Planificar con debug
def _plan_with_debug(x):
    plan = run_planner(x["llm"], x["user_prompt"], x["tools"], max_calls=MAX_CALLS)
    print("\n=== PLAN GENERADO POR EL LLM ===")
    try:
        # Si es Plan de Pydantic, lo serializamos a JSON legible
        if hasattr(plan, "model_dump"):
            print(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False))
        elif isinstance(plan, dict):
            print(json.dumps(plan, indent=2, ensure_ascii=False))
        else:
            print(plan)
    except Exception as e:
        print("Error al imprimir el plan:", e)
    print("================================\n")
    return {**x, "plan": plan}

plan_step = RunnableLambda(_plan_with_debug)

# 3) Ejecutar en paralelo y arrastrar contexto
async def _exec_step(x):
    results_dict, bundle = await execute_plan_parallel(x["plan"], x["registry"])
    print("\n=== RESULTADOS EJECUTADOS ===")
    for tool, res in results_dict.items():
        print(f"\nTool: {tool}")
        try:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        except Exception:
            print(res)
    print("================================\n")
    return {
        "llm": x["llm"],
        "user_prompt": x["user_prompt"],
        "results_dict": results_dict,
        "bundle": bundle,
    }

exec_step = RunnableLambda(_exec_step)

# 4) Finalizer
final_step = RunnableLambda(lambda x: run_finalizer(x["llm"], x["user_prompt"], x["bundle"]))

# Ensamblar pipeline
pipeline = prep_step | plan_step | exec_step | final_step

async def run_planned_parallel(llm: CustomOpenWebLLM, user_prompt: str, tools: list) -> str:
    return await pipeline.ainvoke({"llm": llm, "user_prompt": user_prompt, "tools": tools})