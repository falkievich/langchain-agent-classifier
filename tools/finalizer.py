"""
tools/finalizer.py
──────────────────
Finalizer opcional que usa el LLM para convertir los resultados JSON
en una respuesta en lenguaje natural.

Nota: El LLM aquí NO planifica — solo formatea la respuesta.
La planificación es 100% determinística.
"""
import json
from typing import Any, Dict, List

from classes.custom_llm_classes import get_llm

FINALIZER_SYSTEM = (
    "Eres un asistente jurídico experto. Tu tarea es redactar una respuesta clara y precisa "
    "en ESPAÑOL basándote EXCLUSIVAMENTE en los datos proporcionados.\n\n"
    "REGLAS:\n"
    "- Responde en texto plano, sin Markdown, sin negritas, sin viñetas con asteriscos.\n"
    "- Usa guiones (-) para listar si es necesario.\n"
    "- No menciones nombres de funciones, herramientas ni código.\n"
    "- Si un dato es null o vacío, indica 'No registrado' o 'Sin información'.\n"
    "- Formatea fechas como DD/MM/AAAA.\n"
    "- Sé conciso pero completo.\n"
    "- Si hay errores en los resultados, indícalo claramente.\n"
)

FINALIZER_USER = (
    "Consulta del usuario:\n{user_prompt}\n\n"
    "Datos obtenidos del expediente:\n{bundle_json}\n\n"
    "Redacta la respuesta."
)


def finalize_with_llm(user_prompt: str, result: Dict[str, Any]) -> str:
    """
    Usa el LLM para convertir el resultado de la ejecución en lenguaje natural.
    
    Args:
        user_prompt: consulta original del usuario.
        result: resultado del execute_plan (con steps, records, paths_used).
    """
    # Extraer solo los records de cada step para el LLM
    records_summary = []
    for step in result.get("steps", []):
        records_summary.append({
            "function": step.get("function", ""),
            "domain": step.get("domain", ""),
            "record_count": step.get("record_count", 0),
            "records": step.get("records", []),
        })

    bundle_json = json.dumps(records_summary, ensure_ascii=False, indent=2)

    # Limitar tamaño para no exceder contexto del modelo
    if len(bundle_json) > 15000:
        bundle_json = bundle_json[:15000] + "\n... (datos truncados)"

    llm = get_llm()
    prompt = (
        f"{FINALIZER_SYSTEM}\n\n"
        f"{FINALIZER_USER.format(user_prompt=user_prompt, bundle_json=bundle_json)}"
    )
    return llm._call(prompt=prompt, stop=None)
