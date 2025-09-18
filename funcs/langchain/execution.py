import asyncio, json
from langchain_core.runnables import RunnableLambda, RunnableParallel

# -------- Importaciones --------
# CustomOpenWebLLM: wrapper del LLM para invocar el modelo.
from classes.custom_llm_classes import CustomOpenWebLLM

from funcs.langchain.core import (
    FINALIZER_SYSTEM, FINALIZER_USER_TMPL,  # prompts del finalizador
    BUNDLE_MAX_CHARS,                       # tope de serialización del bundle
    MAX_CONCURRENCY, CALL_TIMEOUT_SEC       # límites de ejecución
)

# -------- Executor --------
# Ejecuta todas las llamadas del Plan en paralelo y devuelve:
# - results_dict: resultados por "call_i" (útil para debug/observabilidad).
# - bundle: lista ordenada [{tool, args, result}, ...] para el finalizer.
# Cada result se normaliza a {"status":"ok","data":...} o {"status":"error","error":...}.

_sem = asyncio.Semaphore(MAX_CONCURRENCY)

async def _maybe_async_call(fn, *args):
    """Ejecuta fn async o sync (empujando sync a thread) sin bloquear el event loop."""
    if asyncio.iscoroutinefunction(fn):
        return await fn(*args)
    return await asyncio.to_thread(fn, *args)

async def _call_with_controls(fn, args, timeout=CALL_TIMEOUT_SEC):
    """Aplica semáforo + timeout y devuelve un dict uniforme de status."""
    async with _sem:
        try:
            data = await asyncio.wait_for(_maybe_async_call(fn, *args), timeout=timeout)
            return {"status": "ok", "data": data}
        except Exception as e:
            return {"status": "error", "error": str(e)}

def _make_call_runnable(fn, args):
    """Crea una rama del fan-out capturando fn+args; cada rama corre con controles."""
    async def _runner(_):
        return await _call_with_controls(fn, args)
    return RunnableLambda(_runner)

async def execute_plan_parallel(plan, registry: dict):
    """Construye el fan-out (RunnableParallel) y ejecuta todas las calls del plan en paralelo."""
    parallel = RunnableParallel({
        f"call_{i}": _make_call_runnable(registry[c.tool], c.args)
        for i, c in enumerate(plan.calls)
    })
    results_dict = await parallel.ainvoke(None)

    # Reempaquetar preservando el orden del plan → insumo directo del finalizer.
    bundle = []
    for i, c in enumerate(plan.calls):
        bundle.append({
            "tool": c.tool,
            "args": c.args,
            "result": results_dict.get(f"call_{i}")
        })
    return results_dict, bundle

# -------- Finalizer --------
# Construye el prompt final con el bundle y obtiene una única respuesta en texto plano.

def run_finalizer(llm: CustomOpenWebLLM, user_prompt: str, bundle: list) -> str:
    """Genera la respuesta final (en español, sin markdown) a partir del bundle completo."""
    # Normalizar uniformidad de result en cada rama.
    for item in bundle:
        if "status" not in item.get("result", {}):
            item["result"] = {"status": "ok", "data": item["result"]}

    # Serializar bundle con tope defensivo para no desbordar el prompt.
    bundle_json = json.dumps(bundle, ensure_ascii=False)[:BUNDLE_MAX_CHARS]

    # Un solo prompt (system+user) → “un thought final” del modelo.
    prompt = FINALIZER_SYSTEM + "\n\n" + FINALIZER_USER_TMPL.format(
        user_prompt=user_prompt,
        bundle_json=bundle_json
    )
    return llm._call(prompt=prompt, stop=None)