import asyncio, json
from langchain_core.runnables import RunnableLambda, RunnableParallel

from funcs.langchain.core import MAX_CONCURRENCY, CALL_TIMEOUT_SEC

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
# Serializa el resultado del Searcher como JSON string.
# Sin LLM. Sin síntesis en lenguaje natural.
#
# El Searcher devuelve siempre:
#   { "op": "...", "resultado": <dict|list> }
#
# El Finalizer lo serializa directamente y lo devuelve al cliente.
def run_finalizer(resultado: dict) -> str:
    """
    Serializa el resultado del Searcher como JSON string.

    Normaliza el resultado para garantizar que siempre tenga
    la misma estructura de salida, independientemente de la operación.

    Args:
        resultado: Dict devuelto por ejecutar_plan().
                   Estructura esperada: { "op": "...", "resultado": ... }

    Returns:
        JSON string con la siguiente estructura:
        {
          "op":        "FIND",
          "resultado": [...],
          "total":     3          ← solo para listas
        }
        o en caso de error:
        {
          "op":    "FIND",
          "error": "mensaje de error"
        }
    """
    # Caso error del Searcher
    if "error" in resultado:
        return json.dumps(resultado, ensure_ascii=False, indent=2)

    op   = resultado.get("op", "UNKNOWN")
    data = resultado.get("resultado")

    salida: dict = {"op": op}

    # Si el resultado es una lista, agregar total
    if isinstance(data, list):
        salida["resultado"] = data
        salida["total"]     = len(data)

    # Si es un dict (GET, COUNT, PIPE)
    elif isinstance(data, dict):
        salida["resultado"] = data

    # Fallback
    else:
        salida["resultado"] = data

    return json.dumps(salida, ensure_ascii=False, indent=2, default=str)
