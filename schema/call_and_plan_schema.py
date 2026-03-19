"""
schema/call_and_plan_schema.py
──────────────────────────────
Modelos Pydantic para el plan de ejecución.

Enfoque: Funciones Semánticas.
El LLM elige función(es) + filtros → el backend ejecuta determinísticamente.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Any, Optional, Dict


class StepFilter(BaseModel):
    """Un filtro a aplicar sobre los datos del dominio."""
    model_config = ConfigDict(extra="ignore")

    field: str = Field(..., description="Campo por el cual filtrar")
    op: str = Field(default="contains", description="Operador: 'eq', 'contains', 'gte', 'lte'")
    value: str = Field(..., description="Valor a comparar (siempre string)")


class Step(BaseModel):
    """
    Un paso del plan semántico.

    Cada step selecciona UNA función semántica con filtros opcionales.
    Los steps pueden encadenarse con depends_on.
    """
    model_config = ConfigDict(extra="ignore")

    step_id: int = Field(..., description="ID numérico del paso (1, 2, 3...)")
    function: str = Field(..., description="Nombre de la función semántica")
    filters: List[StepFilter] = Field(default_factory=list, description="Filtros a aplicar")
    depends_on: Optional[int] = Field(
        default=None,
        description="ID del step del que depende (el resultado del padre filtra el hijo)"
    )


class Plan(BaseModel):
    """Plan ejecutable: secuencia de steps semánticos."""
    model_config = ConfigDict(extra="ignore")

    steps: List[Step] = Field(default_factory=list, description="Pasos del plan")