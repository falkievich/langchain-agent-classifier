from pydantic import BaseModel, Field
from typing import List, Any

# -------- Schema/Models --------
# Modelos Pydantic que definen el contrato del Planner:
# - Call: nombre de tool + args posicionales.
# - Plan: lista de Calls que el Executor correrá en paralelo.

class Call(BaseModel):
    """Una invocación a tool con argumentos posicionales."""
    tool: str = Field(..., description="Nombre exacto de la tool registrada")
    args: List[Any] = Field(default_factory=list, description="Argumentos posicionales")

class Plan(BaseModel):
    """Plan ejecutable: secuencia de llamadas (orden preservado para el bundle)."""
    calls: List[Call] = Field(default_factory=list)