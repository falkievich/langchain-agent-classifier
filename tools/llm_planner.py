"""
tools/llm_planner.py
────────────────────
Planner LLM: genera un plan de funciones semánticas.

El LLM recibe:
  - La consulta del usuario
  - El catálogo de funciones semánticas (nombre + descripción + filtros + paths disponibles)

Y devuelve un plan JSON con steps:
  {
    "steps": [
      {
        "step_id": 1,
        "function": "get_personas",
        "filters": [{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}],
        "output_paths": ["nombre_completo", "vinculos", "numero_documento"]
      }
    ]
  }

IMPORTANTE: El LLM SOLO genera el plan. No ejecuta nada. La ejecución es determinística.
"""
import json
import re
from typing import Any, Dict, List, Optional

from schema.call_and_plan_schema import Plan, Step, StepFilter
from schema.function_catalog import FUNCTION_CATALOG, FUNCTION_AVAILABLE_PATHS


# ═══════════════════════════════════════════════════════════════
#  Catálogo de funciones para el prompt (se genera dinámicamente)
# ═══════════════════════════════════════════════════════════════

def _build_function_catalog() -> str:
    """Genera el catálogo de funciones disponibles para incluir en el system prompt."""
    lines = []
    for fname, meta in FUNCTION_CATALOG.items():
        desc = meta["description"]
        filters = meta.get("filters", {})
        available_paths = FUNCTION_AVAILABLE_PATHS.get(fname, ["*"])

        filters_str = ""
        if filters:
            filter_items = ", ".join(f"{k} ({v})" for k, v in filters.items())
            filters_str = f"\n    Filtros: {filter_items}"

        paths_str = ""
        if available_paths != ["*"]:
            paths_str = f"\n    Paths disponibles: {available_paths}"
        else:
            paths_str = "\n    Paths disponibles: [*] (devuelve todo)"

        lines.append(f"• {fname}\n    {desc}{filters_str}{paths_str}")
    return "\n\n".join(lines)


_FUNCTION_CATALOG_TEXT = _build_function_catalog()


# ═══════════════════════════════════════════════════════════════
#  System prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = f"""Eres un planificador de consultas sobre expedientes judiciales argentinos.
Devuelve SOLO JSON válido. Sin texto adicional, sin markdown, sin backticks.

FUNCIONES DISPONIBLES:
{_FUNCTION_CATALOG_TEXT}

REGLAS GENERALES:
1. Elige la(s) función(es) que mejor responden la consulta.
2. Agrega filtros solo si la consulta especifica una condición (rol, nombre, tipo de contacto).
3. Para preguntas simples: 1 función, 0-1 filtros.
4. Para preguntas compuestas que involucran múltiples entidades independientes: múltiples funciones en paralelo (sin depends_on).
5. No encadenes steps si la respuesta está en una sola función.
6. depends_on SOLO cuando necesitas el resultado del step anterior para filtrar el siguiente.
7. Los values en filters son siempre strings.
8. Operadores: eq (igual exacto) | contains (contiene, case-insensitive) | gte (>=) | lte (<=)

REGLAS DE output_paths:
1. Incluir SOLO los paths que respondan directamente la consulta del usuario.
2. Elegir paths EXACTAMENTE del listado "Paths disponibles" de la función — no abreviar ni inventar nombres.
3. Siempre incluir "nombre_completo" cuando la entidad es persona, abogado o funcionario.
4. Siempre incluir "vinculos" si el filtro fue por vinculo o la consulta pide el rol.
5. Si la consulta pide domicilio/dirección: incluir los sub-campos relevantes (provincia, ciudad, calle), no el objeto domicilios completo.
6. Si la consulta pide contacto (celular/email): incluir digital_clase + descripcion.
7. Siempre copiar el nombre del path tal como aparece en "Paths disponibles". Ejemplos correctos: "ubicacion_actual_codigo", "ubicacion_actual_descripcion". NUNCA abreviar a "ubicacion_actual".
8. No incluir paths que el usuario no pidió (ej: si pide DNI, no incluir fecha_nacimiento).

REGLA ESPECIAL — "abogado de la víctima / del imputado":
  El abogado de una persona está en personas_legajo.relacionados.
  Usar get_abogados_de_persona con filtro vinculos.descripcion_vinculo.
  NO usar get_abogados — esa función trae abogados globales, no embebidos en personas.

REGLA ESPECIAL — "celular/teléfono/email del abogado de la víctima":
  Usar get_contactos_abogados_de_persona con filtro vinculos.descripcion_vinculo + domicilios.digital_clase.

REGLA ESPECIAL — "mayor de edad / no es menor":
  "mayor de edad" equivale a es_menor=false. Usar get_caracteristicas_personas
  con filtro {{"field": "caracteristicas.es_menor", "op": "eq", "value": "false"}}.
  NO usar fecha_nacimiento ni otro campo.

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
      ],
      "output_paths": ["path1", "path2"]
    }}
  ]
}}

EJEMPLOS:

"indicame que persona vive en Corrientes Capital"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_personas",
  "filters": [
    {{"field": "domicilios.domicilio.provincia", "op": "eq", "value": "CORRIENTES"}},
    {{"field": "domicilios.domicilio.ciudad", "op": "eq", "value": "CAPITAL"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "domicilios.domicilio.provincia", "domicilios.domicilio.ciudad", "domicilios.domicilio.calle"]
}}]}}

"DNI del abogado Thiago"
{{"steps": [{{"step_id": 1, "function": "get_abogados",
  "filters": [{{"field": "nombre", "op": "contains", "value": "Thiago"}}],
  "output_paths": ["nombre_completo", "numero_documento"]
}}]}}

"información del expediente"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": [],
  "output_paths": ["cuij", "numero_expediente", "anio_expediente", "tipo_expediente", "estado_expediente_descripcion", "caratula_publica", "etapa_procesal_descripcion", "organismo_descripcion", "ubicacion_actual_codigo", "ubicacion_actual_descripcion"]
}}]}}

"traeme las víctimas"
{{"steps": [{{"step_id": 1, "function": "get_personas",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}],
  "output_paths": ["nombre_completo", "numero_documento", "vinculos"]
}}]}}

"mostrame todos los abogados"
{{"steps": [{{"step_id": 1, "function": "get_abogados", "filters": [],
  "output_paths": ["nombre_completo", "numero_documento", "matricula", "vinculo_descripcion"]
}}]}}

"ficha del fiscal"
{{"steps": [{{"step_id": 1, "function": "get_funcionarios",
  "filters": [{{"field": "cargo", "op": "contains", "value": "fiscal"}}],
  "output_paths": ["nombre_completo", "numero_documento", "cargo"]
}}]}}

"DNI del abogado de la víctima"
{{"steps": [{{"step_id": 1, "function": "get_abogados_de_persona",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}],
  "output_paths": ["nombre_completo", "vinculos", "relacionados.nombre_completo", "relacionados.numero_documento"]
}}]}}

"celular del abogado de la víctima"
{{"steps": [{{"step_id": 1, "function": "get_contactos_abogados_de_persona",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}},
    {{"field": "relacionados.domicilios.digital_clase", "op": "contains", "value": "Celular"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "relacionados.nombre_completo", "relacionados.domicilios.digital_clase", "relacionados.domicilios.descripcion"]
}}]}}

"celular del defensor público"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_abogados",
  "filters": [
    {{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}},
    {{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}
  ],
  "output_paths": ["nombre_completo", "vinculo_descripcion", "domicilios.digital_clase", "domicilios.descripcion"]
}}]}}

"a quién representa el defensor público?"
{{"steps": [{{"step_id": 1, "function": "get_representados_abogados",
  "filters": [{{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}}],
  "output_paths": ["nombre_completo", "vinculo_descripcion", "representados.nombre_completo", "representados.vinculo_descripcion"]
}}]}}

"domicilios de las víctimas"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_personas",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}],
  "output_paths": ["nombre_completo", "vinculos", "domicilios.domicilio.provincia", "domicilios.domicilio.ciudad", "domicilios.domicilio.calle"]
}}]}}

"características de los imputados detenidos"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "imputado"}},
    {{"field": "es_detenido", "op": "eq", "value": "true"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "es_detenido", "caracteristicas.ocupacion", "caracteristicas.estado_civil", "caracteristicas.es_menor"]
}}]}}

"la víctima es mayor de edad?"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}},
    {{"field": "caracteristicas.es_menor", "op": "eq", "value": "false"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "caracteristicas.es_menor"]
}}]}}

"todos los celulares del expediente"
{{"steps": [
  {{"step_id": 1, "function": "get_domicilios_personas",
   "filters": [{{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}],
   "output_paths": ["nombre_completo", "vinculos", "domicilios.digital_clase", "domicilios.descripcion"]}},
  {{"step_id": 2, "function": "get_domicilios_abogados",
   "filters": [{{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}],
   "output_paths": ["nombre_completo", "vinculo_descripcion", "domicilios.digital_clase", "domicilios.descripcion"]}},
  {{"step_id": 3, "function": "get_funcionarios", "filters": [],
   "output_paths": ["nombre_completo", "cargo", "domicilios"]}}
]}}

"domicilio del representado del defensor público"
{{"steps": [
  {{"step_id": 1, "function": "get_representados_abogados",
   "filters": [{{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}}],
   "output_paths": ["nombre_completo", "vinculo_descripcion", "representados.nombre_completo", "representados.numero_documento"]}},
  {{"step_id": 2, "function": "get_domicilios_personas", "filters": [], "depends_on": 1,
   "output_paths": ["nombre_completo", "domicilios.domicilio.provincia", "domicilios.domicilio.ciudad", "domicilios.domicilio.calle"]}}
]}}

"cuál es el CUIJ?"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": [],
  "output_paths": ["cuij", "numero_expediente", "anio_expediente"]
}}]}}

"descripción de la causa"
{{"steps": [{{"step_id": 1, "function": "get_causa", "filters": [],
  "output_paths": ["descripcion", "fecha_hecho", "forma_inicio", "caratula_publica"]
}}]}}

"delitos del expediente"
{{"steps": [{{"step_id": 1, "function": "get_delitos", "filters": [],
  "output_paths": ["codigo", "descripcion"]
}}]}}

"radicaciones del expediente"
{{"steps": [{{"step_id": 1, "function": "get_radicaciones", "filters": [],
  "output_paths": ["organismo_actual_codigo", "organismo_actual_descripcion", "fecha_desde", "fecha_hasta", "motivo_actual_descripcion"]
}}]}}

"dependencias que intervinieron"
{{"steps": [{{"step_id": 1, "function": "get_dependencias", "filters": [],
  "output_paths": ["organismo_descripcion", "dependencia_descripcion", "clase_descripcion", "rol", "activo"]
}}]}}

"dónde está radicado el expediente?"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": [],
  "output_paths": ["ubicacion_actual_codigo", "ubicacion_actual_descripcion", "dependencia_radicacion_codigo", "dependencia_radicacion_descripcion"]
}}]}}

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

    # Parsear output_paths (opcional)
    raw_paths = step_dict.get("output_paths")
    output_paths: Optional[List[str]] = None
    if isinstance(raw_paths, list) and raw_paths and raw_paths != ["*"]:
        # Validar contra los paths disponibles de la función
        available = set(FUNCTION_AVAILABLE_PATHS.get(func_name, []))
        if available and available != {"*"}:
            valid = [p for p in raw_paths if p in available]
            output_paths = valid if valid else None
        else:
            output_paths = raw_paths  # función escalar o sin restricción

    return Step(
        step_id=step_dict.get("step_id", 0),
        function=func_name,
        filters=filters,
        output_paths=output_paths,
        depends_on=step_dict.get("depends_on"),
    )


# ═══════════════════════════════════════════════════════════════
#  API principal
# ═══════════════════════════════════════════════════════════════

def generate_plan_with_llm(user_prompt: str) -> Plan:
    """
    Usa OpenAI para generar un plan de funciones semánticas.

    El system prompt se envía como rol 'system' para que OpenAI lo cachee
    automáticamente (ahorro de hasta ~50 % en tokens de entrada cuando el
    prefijo supera los ~1 024 tokens).

    Returns:
        Plan con steps semánticos.
    """
    from classes.custom_llm_classes import OpenAILLM
    llm = OpenAILLM()
    llm.system_prompt = _SYSTEM_PROMPT   # ← cacheado por OpenAI en llamadas repetidas

    user_text = _USER_TEMPLATE.format(prompt=user_prompt)

    print(f"\n[llm_planner] 🔍 Consulta del usuario: '{user_prompt}'")
    print(f"[llm_planner] 🤖 Modelo: {llm.model}  |  temp={llm.temperature}  |  max_tokens={llm.max_tokens}")

    try:
        raw_response = llm._call(prompt=user_text, stop=None)
    except Exception as e:
        print(f"[llm_planner] ❌ LLM error: {e}")
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
