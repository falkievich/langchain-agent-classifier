import json
import re
from typing import Optional
from pydantic import ValidationError

from classes.custom_llm_classes import CustomOpenWebLLM
from schema.plan_schema import Plan
from funcs.langchain.core import INTERPRETER_SYSTEM, INTERPRETER_USER_TMPL

# -------- Intérprete --------
# Reemplaza al Planner anterior.
#
# Diferencia clave con el Planner viejo:
#   ANTES:  LLM recibe pregunta + lista de tools → elige tool y construye args libremente
#   AHORA:  LLM recibe pregunta + descripción de nodos/operaciones/conceptos disponibles
#           → devuelve un Plan DSL validado por Pydantic
#
# El LLM nunca ve el JSON del expediente.
# El LLM nunca elige funciones Python.
# El LLM solo elige: op + nodo + condiciones → acotado y determinista.


def _extraer_json(raw: str) -> str:
    """
    Extrae el primer bloque JSON válido del texto devuelto por el LLM.
    Maneja casos donde el LLM envuelve el JSON en ```json ... ``` o agrega texto.
    """
    # Caso 1: bloque markdown ```json ... ```
    md_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if md_match:
        return md_match.group(1)

    # Caso 2: JSON directo — buscar desde el primer { hasta el último }
    start = raw.find("{")
    end   = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1]

    raise ValueError(f"No se encontró JSON en la respuesta del LLM.\nRAW:\n{raw}")


def _intentar_parsear(json_str: str) -> dict:
    """
    Intenta parsear el JSON. Si falla, lanza RuntimeError con contexto claro.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"El LLM devolvió JSON malformado.\n"
            f"Error: {e}\n"
            f"JSON recibido:\n{json_str}"
        )


def run_interpreter(llm: CustomOpenWebLLM, user_prompt: str, catalogo_texto: Optional[str] = None, max_reintentos: int = 2) -> Plan:
    """
    Invoca al LLM con la pregunta del usuario y devuelve un Plan validado por Pydantic.

    Flujo:
      1. Construye prompt con INTERPRETER_SYSTEM + catálogo de campos + INTERPRETER_USER_TMPL
      2. LLM devuelve JSON del Plan
      3. Extrae el JSON de la respuesta (maneja texto adicional del LLM)
      4. Valida con Pydantic → si falla, reintenta hasta max_reintentos
      5. Devuelve Plan validado

    Args:
        llm:             Instancia del LLM.
        user_prompt:     Pregunta del usuario en lenguaje natural.
        catalogo_texto:  Catálogo de campos del JSON actual (construido por catalogo.py).
                         Si es None, el LLM opera sin información de campos (modo degradado).
        max_reintentos:  Cuántas veces reintentar si el LLM devuelve JSON inválido.

    Returns:
        Plan validado por Pydantic.

    Raises:
        RuntimeError: Si después de max_reintentos el Plan sigue siendo inválido.
    """
    # Inyectar catálogo en el system prompt si está disponible
    sistema = INTERPRETER_SYSTEM
    if catalogo_texto:
        sistema = (
            f"{INTERPRETER_SYSTEM}\n\n"
            f"## Campos disponibles en este expediente\n"
            f"Usa EXACTAMENTE estos nombres de campo al construir el plan.\n"
            f"No inventes campos que no estén en esta lista.\n\n"
            f"{catalogo_texto}"
        )

    user = INTERPRETER_USER_TMPL.format(user_prompt=user_prompt)
    full_prompt = f"{sistema}\n\n{user}"

    ultimo_error = None

    for intento in range(1, max_reintentos + 1):
        print(f"\n[INTÉRPRETE] Intento {intento}/{max_reintentos}")

        raw = llm._call(prompt=full_prompt, stop=None)
        print(f"[INTÉRPRETE] Respuesta raw del LLM:\n{raw}\n")

        try:
            json_str  = _extraer_json(raw)
            plan_dict = _intentar_parsear(json_str)
            plan      = Plan.model_validate(plan_dict)

            print(f"[INTÉRPRETE] Plan validado correctamente: op={plan.op}")
            return plan

        except (ValueError, RuntimeError) as e:
            ultimo_error = e
            print(f"[INTÉRPRETE] ⚠️  Error de extracción/parseo: {e}")
            continue

        except ValidationError as e:
            ultimo_error = e
            print(f"[INTÉRPRETE] ⚠️  Plan inválido según Pydantic:\n{e}")
            # En el reintento, agregamos el error al prompt para que el LLM se corrija
            full_prompt = (
                f"{sistema}\n\n"
                f"{user}\n\n"
                f"CORRECCIÓN REQUERIDA — tu respuesta anterior fue inválida:\n"
                f"{e}\n"
                f"Corrige el JSON y devuélvelo nuevamente."
            )
            continue

    raise RuntimeError(
        f"El Intérprete no pudo producir un Plan válido después de {max_reintentos} intentos.\n"
        f"Último error: {ultimo_error}"
    )
