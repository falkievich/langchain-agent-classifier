"""
tools/condition_extractor.py
────────────────────────────
Extractor de condiciones/filtros del prompt del usuario usando LLM mínimo.

El LLM aquí NO planifica ni elige tools — solo interpreta la consulta del
usuario y devuelve un JSON estructurado indicando:
  - qué campos quiere ver (data_fields)
  - sobre qué sección del expediente (sections)
  - qué filtros/condiciones aplican (filters)

Ejemplo:
  Prompt:  "domicilios de las víctimas"
  Output:  {
    "sections": ["personas_legajo"],
    "data_fields": ["domicilios"],
    "filters": [{"field": "rol", "operator": "eq", "value": "victima"}]
  }

  Prompt:  "teléfono de los abogados defensores públicos"
  Output:  {
    "sections": ["abogados_legajo"],
    "data_fields": ["domicilios", "telefono"],
    "filters": [{"field": "vinculo_descripcion", "operator": "contains", "value": "defensor publico"}]
  }
"""
import json
import re
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════
#  Schema de condiciones
# ═══════════════════════════════════════════════════════════════

class ConditionFilter:
    """Un filtro individual extraído del prompt."""
    __slots__ = ("field", "operator", "value")

    def __init__(self, field: str, operator: str, value: str):
        self.field = field          # campo del JSON sobre el que filtrar
        self.operator = operator    # eq, contains, gt, lt, gte, lte, ne, exists
        self.value = value          # valor de comparación

    def to_dict(self) -> Dict[str, str]:
        return {"field": self.field, "operator": self.operator, "value": self.value}

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "ConditionFilter":
        return cls(d.get("field", ""), d.get("operator", "eq"), d.get("value", ""))

    def __repr__(self):
        return f"Filter({self.field} {self.operator} {self.value!r})"


class ExtractedConditions:
    """Resultado completo del condition extractor."""
    __slots__ = ("sections", "data_fields", "filters", "raw_intent")

    def __init__(self, sections: List[str], data_fields: List[str],
                 filters: List[ConditionFilter], raw_intent: str = ""):
        self.sections = sections
        self.data_fields = data_fields
        self.filters = filters
        self.raw_intent = raw_intent  # resumen en texto plano de la intención

    def has_filters(self) -> bool:
        return len(self.filters) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sections": self.sections,
            "data_fields": self.data_fields,
            "filters": [f.to_dict() for f in self.filters],
            "raw_intent": self.raw_intent,
        }

    def __repr__(self):
        return f"Conditions(sections={self.sections}, fields={self.data_fields}, filters={self.filters})"


# ═══════════════════════════════════════════════════════════════
#  System prompt para el LLM extractor
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """Eres un parser de consultas sobre expedientes judiciales argentinos.
Tu ÚNICA tarea es analizar la consulta del usuario y devolver un JSON con la estructura que describo abajo.
NO respondas con texto. SOLO devuelve JSON válido.

El expediente tiene estas secciones:
- cabecera_legajo: datos generales (cuij, estado, etapa procesal, tipo proceso, prioridad, caratula, fechas, organismo, secretaria, ubicacion)
- personas_legajo: personas involucradas con sub-datos: vinculos, caracteristicas, calificaciones_legales, relacionados, domicilios
- abogados_legajo: abogados con sub-datos: representados, domicilios
- funcionarios: funcionarios (fiscal, juez) con domicilios/emails
- causa: datos del hecho (descripcion, fecha_hecho, forma_inicio)
- dependencias_vistas: organismos/dependencias con tipos
- radicaciones: radicaciones/movimientos del expediente
- materia_delitos: delitos asociados
- extras: clasificadores, organismo_control, estado_legajo, seguridad

Campos filtrables de personas:
- rol (imputado, victima, actor, demandado, denunciante, querellante, testigo, perito)
- genero (MASCULINO, FEMENINO)
- es_menor (true, false)
- estado_detencion (true, false)
- nombre, apellido, nombre_completo
- numero_documento (DNI)
- cuil
- ocupacion, estado_civil, nivel_educativo, lugar_nacimiento
- vinculo_codigo (IMP, VIC, ACT), vinculo_descripcion (imputado, victima, actor)

Campos filtrables de abogados:
- nombre, apellido
- numero_documento, cuil, matricula
- vinculo_codigo (DPUB, DPRIV), vinculo_descripcion (defensor publico, defensor privado)

Campos filtrables de funcionarios:
- nombre, apellido, cargo (fiscal, juez, secretario)

Campos filtrables de dependencias:
- organismo_descripcion, clase_descripcion, jerarquia, rol, activo

Campos filtrables de radicaciones:
- organismo_descripcion, motivo_descripcion

Campos filtrables de delitos:
- codigo, descripcion, orden

Operadores disponibles: eq, contains, gt, lt, gte, lte, ne, exists

ESTRUCTURA DE RESPUESTA (JSON):
{
  "sections": ["sección1", "sección2"],
  "data_fields": ["campo1", "campo2"],
  "filters": [
    {"field": "campo", "operator": "operador", "value": "valor"}
  ],
  "raw_intent": "resumen breve de la intención"
}

REGLAS:
1. sections: las secciones del expediente involucradas
2. data_fields: los campos o sub-nodos específicos que pide el usuario (ej: "domicilios", "nombre", "telefono", "matricula"). Si pide todo, usa ["*"]
3. filters: condiciones para filtrar los datos. Si no hay filtro, devuelve lista vacía []
4. raw_intent: resumen en español de qué pide el usuario
5. Si el usuario dice "víctimas", es un filtro por rol=victima en personas_legajo
6. Si dice "defensores públicos", es un filtro por vinculo_descripcion en abogados_legajo
7. Si dice "detenidos", es un filtro por estado_detencion=true
8. Si dice "menores", es un filtro por es_menor=true
9. Normaliza los valores a minúsculas sin tildes

SOLO devuelve JSON. Sin texto adicional, sin markdown, sin backticks."""

_USER_TEMPLATE = "Consulta: {prompt}"


# ═══════════════════════════════════════════════════════════════
#  Extracción con LLM
# ═══════════════════════════════════════════════════════════════

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_llm_json(raw: str) -> Dict[str, Any]:
    """Intenta parsear JSON de la respuesta del LLM, tolerando markdown fences."""
    # 1. Buscar bloque ```json ... ```
    m = _JSON_BLOCK_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Buscar primer { ... } en la respuesta
    m = _JSON_OBJECT_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 3. Intentar parsear la respuesta completa
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {}


def extract_conditions_with_llm(user_prompt: str) -> ExtractedConditions:
    """
    Usa el LLM para extraer condiciones/filtros de la consulta del usuario.
    
    El LLM NO planifica — solo interpreta qué quiere el usuario y qué filtros aplica.
    """
    # Lazy import to avoid pulling in heavy dependencies at module level
    from classes.custom_llm_classes import CustomOpenWebLLM
    llm = CustomOpenWebLLM()

    full_prompt = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"{_USER_TEMPLATE.format(prompt=user_prompt)}"
    )

    try:
        raw_response = llm._call(prompt=full_prompt, stop=None)
    except Exception as e:
        # Si falla el LLM, devolver condiciones vacías (fallback determinístico)
        print(f"[condition_extractor] LLM error: {e}")
        return ExtractedConditions(sections=[], data_fields=["*"], filters=[], raw_intent="")

    parsed = _parse_llm_json(raw_response)

    if not parsed:
        print(f"[condition_extractor] No se pudo parsear JSON del LLM: {raw_response[:200]}")
        return ExtractedConditions(sections=[], data_fields=["*"], filters=[], raw_intent="")

    # Construir filtros
    filters = []
    for f in parsed.get("filters", []):
        if isinstance(f, dict) and "field" in f:
            filters.append(ConditionFilter.from_dict(f))

    return ExtractedConditions(
        sections=parsed.get("sections", []),
        data_fields=parsed.get("data_fields", ["*"]),
        filters=filters,
        raw_intent=parsed.get("raw_intent", ""),
    )


# ═══════════════════════════════════════════════════════════════
#  Detección rápida de si se necesita el LLM extractor
# ═══════════════════════════════════════════════════════════════

# Patrones que indican condiciones implícitas en el prompt
_CONDITION_INDICATORS = [
    # Preposiciones que indican filtro sobre un tipo de persona/rol
    r"\b(?:de|del) (?:l[oa]s? )?(?:victima|imputado|actor|demandado|denunciante|querellante|testigo|perito)s?\b",
    r"\b(?:de|del) (?:l[oa]s? )?(?:defensor|abogado)s?\s*(?:publico|privado)s?\b",
    r"\b(?:de|del) (?:l[oa]s? )?(?:fiscal|juez|secretario)(?:es)?\b",
    r"\b(?:de|del) (?:l[oa]s? )?(?:detenid[oa]|pres[oa]|menor)(?:es|s)?\b",
    # "de los menores", "de las mujeres", "de los hombres"
    r"\b(?:de|del) (?:l[oa]s? )?(?:menor|menores|mujer|mujeres|hombre|hombres|varon|varones)\b",
    # Adjetivos/condiciones directos sobre entidades
    r"\bpersonas?\s+(?:detenid[oa]s?|menor(?:es)?|masculin[oa]s?|femenin[oa]s?)\b",
    r"\babogados?\s+(?:publico|privado|defensor)s?\b",
    # "que son", "que sean", "que tienen", "que estén", "que representan"
    r"\bque\s+(?:son|sean|tienen|tengan|est[eé]n|est[aá]n|fueron?|hayan|represent[ae]n?)\b",
    # "solo los/las", "únicamente"
    r"\b(?:solo|solamente|unicamente|únicamente)\s+(?:l[oa]s?)\b",
    # "con cargo de", "con rol de"
    r"\bcon\s+(?:cargo|rol|tipo|estado|genero|género|clase)\s+(?:de\s+)?",
    # "cuyo/cuyos/cuya/cuyas"
    r"\bcuy[oa]s?\b",
    # "donde", "cuando" en contexto condicional
    r"\b(?:donde|cuando|si|en caso)\b.*\b(?:sea|son|tiene|está|haya)\b",
    # Referencia a roles como sustantivo directo con datos
    r"\b(?:datos?|informacion|info|domicilio|telefono|email|direccion|contacto|nombre|dni|cuil)\s+(?:de|del)\s+(?:l[oa]s?\s+)?(?:victima|imputado|actor|demandado|fiscal|juez|abogado|defensor|menor|detenid[oa]|funcionario)s?\b",
    # Inverso: rol + datos
    r"\b(?:victima|imputado|actor|demandado|menor|detenid[oa])s?\s+(?:con|que tienen?|y su)s?\s+(?:domicilio|telefono|email)\b",
]

_CONDITION_RES = [re.compile(p, re.IGNORECASE) for p in _CONDITION_INDICATORS]


def prompt_has_conditions(user_prompt: str) -> bool:
    """
    Detección rápida (sin LLM) de si el prompt contiene condiciones implícitas
    que requieren el extractor LLM.
    
    Returns True si probablemente hay filtros/condiciones en la consulta.
    """
    for pattern in _CONDITION_RES:
        if pattern.search(user_prompt):
            return True
    return False
