from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Optional
from enum import Enum


# -------- Enums --------

class Operacion(str, Enum):
    """
    Operaciones disponibles para el Intérprete.
    El LLM solo puede elegir una de estas.
    """
    GET          = "GET"          # Leer un campo directo de un nodo simple (cabecera_legajo, causa)
    FIND         = "FIND"         # Filtrar items de un nodo lista
    FIND_NESTED  = "FIND_NESTED"  # Filtrar items de un nodo lista + bajar a sub-lista
    COUNT        = "COUNT"        # Contar items que cumplen condiciones
    PIPE         = "PIPE"         # Cruce entre dos nodos (resultado de paso 1 alimenta paso 2)


class OperadorCondicion(str, Enum):
    """
    Operadores disponibles para las condiciones de filtro.
    """
    EQ       = "EQ"       # Igual exacto
    CONTAINS = "CONTAINS" # Contiene el valor (útil para arrays y strings)
    IN       = "IN"       # El valor del campo está en una lista
    GT       = "GT"       # Mayor que (fechas, números)
    LT       = "LT"       # Menor que (fechas, números)


class NodoPrincipal(str, Enum):
    """
    Nodos principales del JSON del expediente.
    El LLM solo puede referenciar estos nodos.
    """
    cabecera_legajo    = "cabecera_legajo"
    causa              = "causa"
    personas_legajo    = "personas_legajo"
    abogados_legajo    = "abogados_legajo"
    funcionarios       = "funcionarios"
    dependencias_vistas = "dependencias_vistas"
    radicaciones       = "radicaciones"
    materia_delitos    = "materia_delitos"


# -------- Condicion --------

class Condicion(BaseModel):
    """
    Una condición de filtro dentro de un WHERE.
    Puede referirse a un campo directo (path) o a un concepto semántico (concept).
    El Normalizer traduce 'concept' a path + valor real antes de ejecutar.
    """
    model_config = ConfigDict(extra='ignore')

    path:       Optional[str]               = Field(None, description="Campo del JSON. Ej: 'rol', 'vinculo_codigo'")
    concept:    Optional[str]               = Field(None, description="Concepto semántico. Ej: 'ROLE.IMPUTADO', 'LAWYER.DEFENSOR'")
    op:         OperadorCondicion           = Field(OperadorCondicion.EQ, description="Operador de comparación")
    value:      Optional[Any]               = Field(None, description="Valor a comparar")
    value_from: Optional[str]               = Field(None, description="Para PIPE: referencia a resultado anterior. Ej: 'paso1.persona_id'")


# -------- Consulta Anidada --------

class ConsultaAnidada(BaseModel):
    """
    Sub-consulta dentro de un item (para FIND_NESTED).
    Ej: dentro de personas_legajo[n], buscar en domicilios donde digital_clase_codigo == CEL
    """
    model_config = ConfigDict(extra='ignore')

    path:   str             = Field(..., description="Nombre de la sub-lista dentro del item. Ej: 'domicilios', 'vinculos'")
    where:  List[Condicion] = Field(default_factory=list)
    select: List[str]       = Field(default_factory=list, description="Campos a devolver de la sub-lista")


# -------- Paso de Consulta (para PIPE) --------

class PasoConsulta(BaseModel):
    """
    Un paso dentro de una operación PIPE.
    Cada paso puede referenciar el resultado del paso anterior via value_from.
    """
    model_config = ConfigDict(extra='ignore')

    as_:    Optional[str]               = Field(None, alias="as", description="Alias para referenciar este resultado en pasos siguientes")
    op:     Operacion                   = Field(..., description="Operación de este paso")
    from_:  Optional[NodoPrincipal]     = Field(None, alias="from", description="Nodo principal a consultar")
    where:  List[Condicion]             = Field(default_factory=list)
    select: List[str]                   = Field(default_factory=list)
    nested: Optional[ConsultaAnidada]   = Field(None)
    limit:  Optional[int]               = Field(None)

    model_config = ConfigDict(extra='ignore', populate_by_name=True)


# -------- Plan Principal --------

class Plan(BaseModel):
    """
    Plan de consulta generado por el Intérprete (LLM).
    Validado por Pydantic antes de ejecutarse.

    Casos de uso:
      GET:         { op: GET,  from: cabecera_legajo, path: "etapa_procesal_descripcion" }
      FIND:        { op: FIND, from: personas_legajo, where: [...], select: [...] }
      FIND_NESTED: { op: FIND_NESTED, from: personas_legajo, where: [...], select: [...], nested: {...} }
      COUNT:       { op: COUNT, from: personas_legajo, where: [...] }
      PIPE:        { op: PIPE, steps: [ paso1, paso2 ] }
    """
    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    op:     Operacion                   = Field(..., description="Tipo de operación")

    # Campos para GET, FIND, FIND_NESTED, COUNT
    from_:  Optional[NodoPrincipal]     = Field(None, alias="from",   description="Nodo principal")
    path:   Optional[str]               = Field(None,                  description="Para GET: campo directo. Ej: 'etapa_procesal_descripcion'")
    where:  List[Condicion]             = Field(default_factory=list,  description="Condiciones de filtro")
    select: List[str]                   = Field(default_factory=list,  description="Campos a devolver")
    nested: Optional[ConsultaAnidada]   = Field(None,                  description="Para FIND_NESTED: sub-consulta")
    limit:  Optional[int]               = Field(None,                  description="Límite de resultados")

    # Campos para PIPE
    steps:  Optional[List[PasoConsulta]] = Field(None,                 description="Para PIPE: lista de pasos encadenados")
