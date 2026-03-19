"""
tools/llm_planner.py
────────────────────
Planner LLM: genera un plan de funciones semánticas.

El LLM recibe:
  - La consulta del usuario
  - El catálogo de funciones semánticas (nombre + descripción + filtros)

Y devuelve un plan JSON con steps:
  {
    "steps": [
      {"step_id": 1, "function": "get_personas",
       "filters": [{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}]
      }
    ]
  }

IMPORTANTE: El LLM SOLO genera el plan. No ejecuta nada. La ejecución es determinística.
"""
import json
import re
from typing import Any, Dict, List, Optional

from schema.call_and_plan_schema import Plan, Step, StepFilter
from schema.function_catalog import FUNCTION_CATALOG


# ═══════════════════════════════════════════════════════════════
#  Catálogo de funciones para el prompt (se genera dinámicamente)
# ═══════════════════════════════════════════════════════════════

def _build_function_catalog() -> str:
    """Genera el catálogo de funciones disponibles para incluir en el system prompt."""
    lines = []
    for fname, meta in FUNCTION_CATALOG.items():
        desc = meta["description"]
        filters = meta.get("filters", {})
        filters_str = ""
        if filters:
            filter_items = ", ".join(f"{k} ({v})" for k, v in filters.items())
            filters_str = f"\n    Filtros: {filter_items}"
        lines.append(f"• {fname}\n    {desc}{filters_str}")
    return "\n\n".join(lines)


_FUNCTION_CATALOG_TEXT = _build_function_catalog()


# ═══════════════════════════════════════════════════════════════
#  System prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = f"""Eres un planificador de consultas sobre expedientes judiciales argentinos.
Devuelve SOLO JSON válido. Sin texto adicional, sin markdown, sin backticks.

FUNCIONES DISPONIBLES:
{_FUNCTION_CATALOG_TEXT}

REGLAS:
1. Elige la(s) función(es) que mejor responden la consulta.
2. Agrega filtros solo si la consulta especifica una condición (rol, nombre, tipo de contacto).
3. Para preguntas simples: 1 función, 0-1 filtros.
4. Para preguntas compuestas que involucran múltiples entidades independientes: múltiples funciones en paralelo (sin depends_on).
5. No encadenes steps si la respuesta está en una sola función.
6. depends_on SOLO cuando necesitas el resultado del step anterior para filtrar el siguiente.
7. Los values en filters son siempre strings.
8. Operadores: eq (igual exacto) | contains (contiene, case-insensitive) | gte (>=) | lte (<=)

REGLA ESPECIAL — "abogado de la víctima / del imputado":
  El abogado de una persona está en personas_legajo.relacionados.
  Usar get_abogados_de_persona con filtro vinculos.descripcion_vinculo.
  NO usar get_abogados — esa función trae abogados globales, no embebidos en personas.

REGLA ESPECIAL — "celular/teléfono/email del abogado de la víctima":
  Usar get_contactos_abogados_de_persona con filtro vinculos.descripcion_vinculo + domicilios.digital_clase.

REGLA ESPECIAL — "todos los celulares del expediente":
  Lanzar steps INDEPENDIENTES (sin depends_on) para:
  - get_domicilios_personas (filtro domicilios.digital_clase = Celular)
  - get_domicilios_abogados (filtro domicilios.digital_clase = Celular)
  - get_funcionarios (sin filtro, los funcionarios solo tienen email)

ESTRUCTURA:
{{
  "steps": [
    {{
      "step_id": 1,
      "function": "nombre_funcion",
      "filters": [
        {{"field": "campo", "op": "operador", "value": "valor"}}
      ]
    }}
  ]
}}

EJEMPLOS:

"DNI del abogado Thiago"
{{"steps": [{{"step_id": 1, "function": "get_abogados",
  "filters": [{{"field": "nombre", "op": "contains", "value": "Thiago"}}]}}]}}

"información del expediente"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": []}}]}}

"traeme las víctimas"
{{"steps": [{{"step_id": 1, "function": "get_personas",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}]}}]}}

"mostrame todos los abogados"
{{"steps": [{{"step_id": 1, "function": "get_abogados", "filters": []}}]}}

"ficha del fiscal"
{{"steps": [{{"step_id": 1, "function": "get_funcionarios",
  "filters": [{{"field": "cargo", "op": "contains", "value": "fiscal"}}]}}]}}

"DNI del abogado de la víctima"
{{"steps": [{{"step_id": 1, "function": "get_abogados_de_persona",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}]}}]}}

"celular del abogado de la víctima"
{{"steps": [{{"step_id": 1, "function": "get_contactos_abogados_de_persona",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}},
    {{"field": "relacionados.domicilios.digital_clase", "op": "contains", "value": "Celular"}}
  ]}}]}}

"celular del defensor público"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_abogados",
  "filters": [
    {{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}},
    {{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}
  ]}}]}}

"a quién representa el defensor público?"
{{"steps": [{{"step_id": 1, "function": "get_representados_abogados",
  "filters": [{{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}}]}}]}}

"domicilios de las víctimas"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_personas",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}]}}]}}

"características de los imputados detenidos"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "imputado"}},
    {{"field": "es_detenido", "op": "eq", "value": "true"}}
  ]}}]}}

"todos los celulares del expediente"
{{"steps": [
  {{"step_id": 1, "function": "get_domicilios_personas",
   "filters": [{{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}]}},
  {{"step_id": 2, "function": "get_domicilios_abogados",
   "filters": [{{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}]}},
  {{"step_id": 3, "function": "get_funcionarios", "filters": []}}
]}}

"domicilio del representado del defensor público"
{{"steps": [
  {{"step_id": 1, "function": "get_representados_abogados",
   "filters": [{{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}}]}},
  {{"step_id": 2, "function": "get_domicilios_personas", "filters": [], "depends_on": 1}}
]}}

"cuál es el CUIJ?"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": []}}]}}

"descripción de la causa"
{{"steps": [{{"step_id": 1, "function": "get_causa", "filters": []}}]}}

"delitos del expediente"
{{"steps": [{{"step_id": 1, "function": "get_delitos", "filters": []}}]}}

"radicaciones del expediente"
{{"steps": [{{"step_id": 1, "function": "get_radicaciones", "filters": []}}]}}

"dependencias que intervinieron"
{{"steps": [{{"step_id": 1, "function": "get_dependencias", "filters": []}}]}}

SOLO devuelve JSON."""


_USER_TEMPLATE = "Consulta: {prompt}"


# ═══════════════════════════════════════════════════════════════
#  Parsing de la respuesta del LLM
# ═══════════════════════════════════════════════════════════════

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_llm_json(raw: str) -> Dict[str, Any]:
    """Intenta parsear JSON de la respuesta del LLM."""
    # 1. Bloques de código
    m = _JSON_BLOCK_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Primer JSON object
    m = _JSON_OBJECT_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 3. Directo
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {}


def _validate_step(step_dict: Dict[str, Any]) -> Optional[Step]:
    """Valida que un step tenga función válida y lo construye."""
    func_name = step_dict.get("function", "")
    if func_name not in FUNCTION_CATALOG:
        print(f"[llm_planner] Función desconocida: {func_name}")
        return None

    # Parsear filtros
    filters = []
    for f in step_dict.get("filters", []):
        if isinstance(f, dict) and "field" in f and "value" in f:
            filters.append(StepFilter(
                field=f["field"],
                op=f.get("op", "contains"),
                value=str(f["value"]),
            ))

    return Step(
        step_id=step_dict.get("step_id", 0),
        function=func_name,
        filters=filters,
        depends_on=step_dict.get("depends_on"),
    )


# ═══════════════════════════════════════════════════════════════
#  API principal
# ═══════════════════════════════════════════════════════════════

def generate_plan_with_llm(user_prompt: str) -> Plan:
    """
    Usa el LLM para generar un plan de funciones semánticas.

    Returns:
        Plan con steps semánticos.
    """
    from classes.custom_llm_classes import CustomOpenWebLLM
    llm = CustomOpenWebLLM()

    full_prompt = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"{_USER_TEMPLATE.format(prompt=user_prompt)}"
    )

    try:
        raw_response = llm._call(prompt=full_prompt, stop=None)
    except Exception as e:
        print(f"[llm_planner] LLM error: {e}")
        return Plan(steps=[])

    parsed = _parse_llm_json(raw_response)
    if not parsed:
        print(f"[llm_planner] No se pudo parsear: {raw_response[:300]}")
        return Plan(steps=[])

    # Construir steps
    steps = []
    raw_steps = parsed.get("steps", [])
    for s in raw_steps:
        if isinstance(s, dict):
            step = _validate_step(s)
            if step:
                steps.append(step)

    if not steps:
        print("[llm_planner] Plan sin steps válidos")
        return Plan(steps=[])

    return Plan(steps=steps)
