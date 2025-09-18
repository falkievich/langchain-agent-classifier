# -------- schema.py --------
from pydantic import BaseModel, Field
from typing import List, Any

class Call(BaseModel):
    tool: str = Field(..., description="Nombre exacto de la tool registrada")
    args: List[Any] = Field(default_factory=list, description="Argumentos posicionales")

class Plan(BaseModel):
    calls: List[Call] = Field(default_factory=list)
