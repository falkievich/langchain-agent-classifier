import json
from classes.custom_llm_classes import CustomOpenWebLLM
from funcs.langchain.catalogo import construir_catalogo, catalogo_a_texto
from funcs.langchain.interpreter import run_interpreter
from funcs.langchain.normalizer import normalizar_plan
from funcs.langchain.searcher import ejecutar_plan
from funcs.langchain.execution import run_finalizer

# -------- Pipeline --------
# Nuevo flujo determinista: Intérprete → Normalizer → Searcher → Finalizer
#
# Paso 1 — Intérprete (LLM acotado):
#   Recibe solo la pregunta del usuario.
#   Devuelve un Plan DSL validado por Pydantic.
#   El LLM nunca ve el JSON del expediente.
#   El LLM nunca elige funciones Python.
#
# Paso 2 — Normalizer (código puro):
#   Traduce conceptos semánticos a valores reales del JSON.
#   Normaliza tildes, mayúsculas, género y plural.
#
# Paso 3 — Searcher (código puro):
#   Ejecuta el Plan normalizado sobre el JSON.
#   Soporta GET, FIND, FIND_NESTED, COUNT, PIPE.
#
# Paso 4 — Finalizer (código puro):
#   Serializa el resultado como JSON string.
#   Sin LLM. Sin síntesis en lenguaje natural.


async def run_pipeline(llm: CustomOpenWebLLM, user_prompt: str, json_data: dict) -> str:
    """
    Orquesta el flujo completo y devuelve el resultado como JSON string.

    Args:
        llm:         Instancia del LLM (solo lo usa el Intérprete).
        user_prompt: Pregunta del usuario en lenguaje natural.
        json_data:   JSON completo del expediente.

    Returns:
        JSON string con el resultado de la búsqueda.
    """

    # ── Paso 1: Intérprete ───────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("[PIPELINE] PASO 1 — Intérprete")
    print(f"[PIPELINE] Pregunta: {user_prompt}")

    # Construir catálogo de campos del JSON actual
    catalogo     = construir_catalogo(json_data)
    cat_texto    = catalogo_a_texto(catalogo)

    print(f"[PIPELINE] Catálogo construido: {len(catalogo)} nodos")

    plan_raw = run_interpreter(llm, user_prompt, catalogo_texto=cat_texto)

    print(f"[PIPELINE] Plan producido: op={plan_raw.op}")

    # ── Paso 2: Normalizer ───────────────────────────────────────────────────
    print("\n[PIPELINE] PASO 2 — Normalizer")

    plan_normalizado = normalizar_plan(plan_raw)

    # ── Paso 3: Searcher ─────────────────────────────────────────────────────
    print("\n[PIPELINE] PASO 3 — Searcher")

    resultado = ejecutar_plan(json_data, plan_normalizado)

    # ── Paso 4: Finalizer ────────────────────────────────────────────────────
    print("\n[PIPELINE] PASO 4 — Finalizer")

    respuesta = run_finalizer(resultado)

    print("\n[PIPELINE] Completado.")
    print("═" * 60)

    return respuesta