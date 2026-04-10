"""
schema/call_and_plan_schema.py
──────────────────────────────
Modelos Pydantic para el plan de ejecución.

Enfoque: Funciones Semánticas.
El LLM elige función(es) + filtros + output_paths → el backend ejecuta determinísticamente.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Any, Optional, Dict


class StepFilter(BaseModel):
    """Un filtro a aplicar sobre los datos del dominio."""
    model_config = ConfigDict(extra="ignore")

    field: str = Field(..., description="Campo por el cual filtrar")
    op: str = Field(default="contains", description="Operador: 'eq', 'contains', 'gte', 'lte', 'neq'")
    value: str = Field(..., description="Valor a comparar (siempre string)")


class Step(BaseModel):
    """
    Un paso del plan semántico.

    Cada step selecciona UNA función semántica con filtros opcionales
    y los paths exactos que se quieren devolver.
    Los steps pueden encadenarse con depends_on.

    Operadores lógicos:
      filter_op   : "AND" (default) | "OR"  — cómo se combinan los filtros entre sí.
      negate      : False (default) | True  — niega el grupo completo (NOT).
      same_entity : False (default) | True  — todos los filtros deben cumplirse
                    sobre el MISMO elemento del array (evita falsos positivos
                    donde cada condición la cumple una entidad distinta).
    """
    model_config = ConfigDict(extra="ignore")

    step_id: int = Field(..., description="ID numérico del paso (1, 2, 3...)")
    function: str = Field(..., description="Nombre de la función semántica")
    filters: List[StepFilter] = Field(default_factory=list, description="Filtros a aplicar")
    filter_op: str = Field(
        default="AND",
        description="Operador lógico entre filtros: 'AND' (todos) | 'OR' (al menos uno)",
    )
    negate: bool = Field(
        default=False,
        description="Si True, niega el grupo completo (NOT): excluye los registros que cumplan los filtros",
    )
    same_entity: bool = Field(
        default=False,
        description=(
            "Si True, todos los filtros deben cumplirse sobre el MISMO sub-elemento "
            "de una lista anidada (ej: mismo objeto dentro de 'vinculos'). "
            "Evita falsos positivos donde cada condición la cumple una entidad distinta."
        ),
    )
    output_paths: Optional[List[str]] = Field(
        default=None,
        description=(
            "Paths a incluir en la respuesta (relativos al dominio). "
            "Si es None o ['*'], se devuelven todos los paths de la función."
        ),
    )
    depends_on: Optional[int] = Field(
        default=None,
        description="ID del step del que depende (el resultado del padre filtra el hijo)"
    )


class Plan(BaseModel):
    """Plan ejecutable: secuencia de steps semánticos."""
    model_config = ConfigDict(extra="ignore")

    steps: List[Step] = Field(default_factory=list, description="Pasos del plan")