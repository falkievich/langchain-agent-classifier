"""
tools/llm_planner.py
────────────────────
Planner LLM mínimo: genera un plan SECUENCIAL con dependencias entre pasos.

El LLM recibe:
  - La consulta del usuario
  - El catálogo de tools disponibles (nombres + descripciones)

Y devuelve un plan JSON con steps que se encadenan:

Ejemplo para "domicilios de las víctimas":
  {
    "steps": [
      {"step_id": 1, "tool": "buscar_persona_por_rol", "args": ["victima"]},
      {"step_id": 2, "tool": "listar_domicilios_personas", "args": [], "depends_on": 1, "output_field": "domicilios"}
    ]
  }

Esto significa:
  1. Ejecutar buscar_persona_por_rol("victima") → obtener personas víctima
  2. Ejecutar listar_domicilios_personas PERO filtrando solo sobre las personas del paso 1
     y devolviendo solo el sub-campo "domicilios"

IMPORTANTE: El LLM SOLO genera el plan. No ejecuta nada. La ejecución es determinística.
"""
import json
import re
from typing import Any, Dict, List, Optional

from schema.call_and_plan_schema import Plan, Step
from extractors.registry import TOOL_REGISTRY, TOOL_BY_NAME

# ═══════════════════════════════════════════════════════════════
#  Catálogo de tools para el prompt
# ═══════════════════════════════════════════════════════════════

def _build_tool_catalog() -> str:
    """Genera el catálogo de tools disponibles para incluir en el system prompt."""
    lines = []
    for t in TOOL_REGISTRY:
        args_desc = f"(json_data, {t.keywords[0] if t.keywords else 'arg'})" if t.args > 0 else "(json_data)"
        lines.append(f"- {t.name}{args_desc}: {t.description} [sección: {t.section}]")
    return "\n".join(lines)


_TOOL_CATALOG = _build_tool_catalog()

# ═══════════════════════════════════════════════════════════════
#  System prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = f"""Eres un planificador de consultas sobre expedientes judiciales argentinos.
Tu ÚNICA tarea es generar un plan de ejecución en formato JSON.
NO respondas con texto. SOLO devuelve JSON válido.

TOOLS DISPONIBLES:
{_TOOL_CATALOG}

REGLAS DEL PLAN:
1. Cada step tiene: step_id (entero), tool (nombre exacto), args (lista de argumentos fijos)
2. Un step puede depender de otro usando depends_on (step_id del paso anterior)
3. Si un step depende de otro, su resultado se FILTRARÁ usando los resultados del paso anterior
4. output_field indica qué sub-campo devolver del resultado (ej: "domicilios", "vinculos", "caracteristicas")
5. Usa el MÍNIMO de steps necesarios. No agregues pasos innecesarios.
6. Si la consulta es simple (sin condiciones), usa UN solo step.
7. Si hay condiciones (ej: "de las víctimas", "del imputado", "de los detenidos"), usa DOS steps:
   - Step 1: filtrar las entidades (ej: buscar_persona_por_rol con "victima")
   - Step 2: obtener el dato deseado (ej: listar_domicilios_personas), con depends_on=1
8. Los args son SIEMPRE strings.
9. Para filtrar por rol usa buscar_persona_por_rol con args ["victima"], ["imputado"], etc.
10. Para filtrar abogados por tipo usa buscar_abogado_por_vinculo_descripcion con args ["defensor publico"], etc.
11. Para filtrar funcionarios por cargo usa buscar_funcionario_por_cargo con args ["fiscal"], ["juez"], etc.

ESTRUCTURA DE RESPUESTA:
{{
  "steps": [
    {{"step_id": 1, "tool": "nombre_tool", "args": ["arg1"]}},
    {{"step_id": 2, "tool": "nombre_tool", "args": [], "depends_on": 1, "output_field": "campo"}}
  ]
}}

EJEMPLOS:

Consulta: "cuál es el CUIJ?"
{{"steps": [{{"step_id": 1, "tool": "obtener_cuij", "args": []}}]}}

Consulta: "domicilios de las víctimas"
{{"steps": [
  {{"step_id": 1, "tool": "buscar_persona_por_rol", "args": ["victima"]}},
  {{"step_id": 2, "tool": "listar_domicilios_personas", "args": [], "depends_on": 1, "output_field": "domicilios"}}
]}}

Consulta: "teléfono del fiscal"
{{"steps": [
  {{"step_id": 1, "tool": "buscar_funcionario_por_cargo", "args": ["fiscal"]}},
  {{"step_id": 2, "tool": "listar_domicilios_funcionarios", "args": [], "depends_on": 1, "output_field": "domicilios"}}
]}}

Consulta: "nombre de los abogados defensores públicos"
{{"steps": [
  {{"step_id": 1, "tool": "buscar_abogado_por_vinculo_descripcion", "args": ["defensor publico"]}}
]}}

Consulta: "a quién representa el defensor público?"
{{"steps": [
  {{"step_id": 1, "tool": "buscar_abogado_por_vinculo_descripcion", "args": ["defensor publico"]}},
  {{"step_id": 2, "tool": "listar_representados", "args": [], "depends_on": 1}}
]}}

Consulta: "características de los imputados detenidos"
{{"steps": [
  {{"step_id": 1, "tool": "buscar_persona_por_rol", "args": ["imputado"]}},
  {{"step_id": 2, "tool": "buscar_persona_por_estado_detencion", "args": ["true"], "depends_on": 1}},
  {{"step_id": 3, "tool": "listar_caracteristicas_personas", "args": [], "depends_on": 2, "output_field": "caracteristicas"}}
]}}

SOLO devuelve JSON. Sin texto, sin markdown, sin backticks."""


_USER_TEMPLATE = "Consulta: {prompt}"

# ═══════════════════════════════════════════════════════════════
#  Parsing de la respuesta del LLM
# ═══════════════════════════════════════════════════════════════

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_llm_json(raw: str) -> Dict[str, Any]:
    """Intenta parsear JSON de la respuesta del LLM."""
    m = _JSON_BLOCK_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    m = _JSON_OBJECT_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {}


def _validate_step(step_dict: Dict[str, Any]) -> Optional[Step]:
    """Valida que un step tenga tool válida y lo construye."""
    tool_name = step_dict.get("tool", "")
    if tool_name not in TOOL_BY_NAME:
        print(f"[llm_planner] Tool desconocida: {tool_name}")
        return None

    return Step(
        step_id=step_dict.get("step_id", 0),
        tool=tool_name,
        args=[str(a) for a in step_dict.get("args", [])],
        depends_on=step_dict.get("depends_on"),
        extract_field=step_dict.get("extract_field"),
        output_field=step_dict.get("output_field"),
    )


# ═══════════════════════════════════════════════════════════════
#  API principal
# ═══════════════════════════════════════════════════════════════

def generate_plan_with_llm(user_prompt: str) -> Plan:
    """
    Usa el LLM para generar un plan de ejecución secuencial con dependencias.
    
    El LLM decide:
    - Qué tools ejecutar
    - En qué orden
    - Qué dependencias hay entre pasos
    
    Returns:
        Plan con steps secuenciales.
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
        # Fallback: plan vacío, el pipeline usará el router determinístico
        return Plan(calls=[], steps=[])

    parsed = _parse_llm_json(raw_response)
    if not parsed:
        print(f"[llm_planner] No se pudo parsear: {raw_response[:300]}")
        return Plan(calls=[], steps=[])

    # Construir steps
    steps = []
    raw_steps = parsed.get("steps", [])
    for s in raw_steps:
        if isinstance(s, dict):
            step = _validate_step(s)
            if step:
                steps.append(step)

    if not steps:
        print(f"[llm_planner] Plan sin steps válidos")
        return Plan(calls=[], steps=[])

    return Plan(calls=[], steps=steps)
