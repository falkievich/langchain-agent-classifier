from pydantic import BaseModel, Field, ConfigDict
from typing import List, Any, Optional

# -------- Schema/Models --------
# Modelos Pydantic que definen el contrato del Planner:
# - Call: nombre de tool + args posicionales.
# - Step: un paso del plan que puede tener dependencias de pasos anteriores.
# - Plan: lista de Calls (paralelas) O lista de Steps (secuenciales con dependencias).

class Call(BaseModel):
    """Una invocación a tool con argumentos posicionales."""
    model_config = ConfigDict(extra='ignore')

    tool: str = Field(..., description="Nombre exacto de la tool registrada")
    args: List[Any] = Field(default_factory=list, description="Argumentos posicionales")


class Step(BaseModel):
    """
    Un paso del plan secuencial.
    
    Cada step tiene un id, una tool a ejecutar, y opcionalmente:
    - depends_on: id del step anterior del cual obtener datos
    - extract_field: campo a extraer del resultado del step anterior para usar como argumento
    - output_field: sub-campo del resultado a devolver (ej: "domicilios")
    """
    model_config = ConfigDict(extra='ignore')

    step_id: int = Field(..., description="ID numérico del paso (1, 2, 3...)")
    tool: str = Field(..., description="Nombre exacto de la tool registrada")
    args: List[Any] = Field(default_factory=list, description="Argumentos fijos (si los hay)")
    depends_on: Optional[int] = Field(default=None, description="ID del step del que depende")
    extract_field: Optional[str] = Field(default=None, description="Campo a extraer del resultado del step anterior para usar como argumento")
    output_field: Optional[str] = Field(default=None, description="Sub-campo del resultado a devolver como salida de este step")


class Plan(BaseModel):
    """Plan ejecutable: secuencia de llamadas (orden preservado para el bundle)."""
    model_config = ConfigDict(extra='ignore')

    calls: List[Call] = Field(default_factory=list)
    steps: List[Step] = Field(default_factory=list, description="Pasos secuenciales con dependencias (alternativa a calls)")