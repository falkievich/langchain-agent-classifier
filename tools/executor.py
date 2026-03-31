"""
tools/executor.py
─────────────────
Ejecutor que delega al query_executor determinístico.

Mantiene la interfaz async para compatibilidad con el pipeline,
pero la ejecución real es síncrona y determinística.
"""
import asyncio
from typing import Any, Dict

from schema.call_and_plan_schema import Plan
from tools.query_executor import execute_plan as _execute_plan_sync


async def execute_plan(plan: Plan, json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ejecuta un plan de funciones semánticas.

    Wrapper async sobre el executor determinístico síncrono.

    Returns:
        Dict con steps ejecutados, paths usados y total de registros.
    """
    # Ejecutar en thread para no bloquear el event loop
    result = await asyncio.to_thread(_execute_plan_sync, plan, json_data)
    return result
