"""
tools/deterministic_router.py
─────────────────────────────
Router determinístico — fallback mínimo para cuando el LLM falla.

Flujo:
  1. Normaliza el prompt del usuario.
  2. Intenta matchear alguno de los DIRECT_PATTERNS (regex de alta certeza).
  3. Si hay match → construye un step con filtros extraídos del prompt.
  4. Si no hay match → devuelve get_cabecera como fallback genérico.

NOTA: Este router ya no hace scoring por keywords.
Todo el razonamiento semántico lo hace el LLM (llm_planner.py).
Este módulo solo actúa cuando el LLM falla completamente.
"""
import re
from typing import Dict, List, Tuple

from funcs.helpers_and_utility.langchain_utility import normalize_and_clean
from schema.call_and_plan_schema import Plan, Step, StepFilter
from schema.function_catalog import FUNCTION_CATALOG


# ═══════════════════════════════════════════════════════════════
#  Patrones directos (máxima certeza, sin scoring)
# ═══════════════════════════════════════════════════════════════

DIRECT_PATTERNS: List[Tuple[str, str, List[Dict[str, str]]]] = [
    # (regex, function_name, filtros fijos)
    (r"(?:cual|que) (?:es )?(?:el )?cuij",                   "get_cabecera",         []),
    (r"(?:cual|que) (?:es )?(?:el )?estado (?:del )?expediente", "get_cabecera",      []),
    (r"(?:cual|que) (?:es )?(?:la )?etapa procesal",          "get_cabecera",         []),
    (r"(?:cual|que) (?:es )?(?:la )?prioridad",               "get_cabecera",         []),
    (r"(?:cual|que) (?:es )?(?:la )?caratula",                "get_cabecera",         []),
    (r"(?:informacion|datos).*expediente",                    "get_cabecera",         []),
    (r"(?:cuando|fecha).*hecho",                              "get_causa",            []),
    (r"(?:como|forma).*inicio.*causa",                        "get_causa",            []),
    (r"organismo (?:de )?control",                            "get_organismo_control",[]),
    (r"\b(?:iurixweb|iurixcl|themis|criminis)\b",             "get_datos_sistema",    []),
    (r"(?:de que|que) sistema",                               "get_datos_sistema",    []),
    (r"(?:todos los )?(?:delitos|materias)(?: del expediente)?","get_delitos",         []),
    (r"radicaciones? (?:del expediente|historial)",           "get_radicaciones",     []),
    (r"(?:todos los )?(?:abogados|defensores)(?: del expediente)?","get_abogados",     []),
    (r"(?:todos los )?funcionarios(?: del expediente)?",      "get_funcionarios",     []),
    (r"(?:todas las )?personas(?: del expediente)?",          "get_personas",         []),
]


# ═══════════════════════════════════════════════════════════════
#  Extracción de filtros del prompt
# ═══════════════════════════════════════════════════════════════

_ROLES           = ["imputado", "victima", "actor", "demandado", "denunciante", "querellante", "testigo"]
_CARGOS          = ["fiscal", "juez", "secretario"]
_TIPOS_DEFENSOR  = ["defensor publico", "defensor privado"]
_CONTACTOS       = ["celular", "telefono", "email"]

_DNI_RE    = re.compile(r"\b(\d{7,8})\b")
_QUOTED_RE = re.compile(r'["\']([^"\']+)["\']')
_NAME_RE   = re.compile(
    r"(?:llamad[oa]|nombre|apellido|persona|abogado|funcionario)\s+"
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)"
)


def _extract_filters_from_prompt(prompt: str, function_name: str) -> List[StepFilter]:
    """Intenta extraer filtros del prompt para la función dada."""
    prompt_lower = normalize_and_clean(prompt)
    filters = []
    available_filters = FUNCTION_CATALOG.get(function_name, {}).get("filters", {})

    # Rol procesal
    if "vinculos.descripcion_vinculo" in available_filters:
        for rol in _ROLES:
            if rol in prompt_lower:
                filters.append(StepFilter(field="vinculos.descripcion_vinculo", op="contains", value=rol))
                break

    # Cargo (funcionarios)
    if "cargo" in available_filters:
        for cargo in _CARGOS:
            if cargo in prompt_lower:
                filters.append(StepFilter(field="cargo", op="contains", value=cargo))
                break

    # Tipo de defensor
    if "vinculo_descripcion" in available_filters:
        for tipo in _TIPOS_DEFENSOR:
            if tipo in prompt_lower:
                filters.append(StepFilter(field="vinculo_descripcion", op="contains", value=tipo))
                break

    # Tipo de contacto
    for contact_field in ["domicilios.digital_clase", "relacionados.domicilios.digital_clase"]:
        if contact_field in available_filters:
            for contacto in _CONTACTOS:
                if contacto in prompt_lower:
                    filters.append(StepFilter(field=contact_field, op="contains", value=contacto.capitalize()))
                    break
            break

    # Detenido
    if "es_detenido" in available_filters:
        if any(w in prompt_lower for w in ("detenido", "detenida", "preso")):
            filters.append(StepFilter(field="es_detenido", op="eq", value="true"))

    # Nombre (entre comillas o patrón)
    if "nombre" in available_filters or "nombre_completo" in available_filters:
        field = "nombre_completo" if "nombre_completo" in available_filters else "nombre"
        quoted = _QUOTED_RE.findall(prompt)
        if quoted:
            filters.append(StepFilter(field=field, op="contains", value=quoted[0]))
        else:
            m = _NAME_RE.search(prompt)
            if m:
                filters.append(StepFilter(field=field, op="contains", value=m.group(1).strip()))

    # DNI
    if "numero_documento" in available_filters:
        m = _DNI_RE.search(prompt)
        if m:
            filters.append(StepFilter(field="numero_documento", op="eq", value=m.group(1)))

    return filters


# ═══════════════════════════════════════════════════════════════
#  Router principal
# ═══════════════════════════════════════════════════════════════

def route_query(user_prompt: str) -> Plan:
    """
    Fallback mínimo: solo se ejecuta cuando el LLM falla completamente.

    1. Intenta matchear DIRECT_PATTERNS (regex de alta certeza).
    2. Si hay match → devuelve un plan con ese step + filtros extraídos.
    3. Si no hay match → devuelve get_cabecera como plan genérico de último recurso.
    """
    prompt_norm = normalize_and_clean(user_prompt)

    for pattern, func_name, fixed_filters in DIRECT_PATTERNS:
        if re.search(pattern, prompt_norm):
            filters = (
                [StepFilter(**f) for f in fixed_filters]
                if fixed_filters
                else _extract_filters_from_prompt(user_prompt, func_name)
            )
            return Plan(steps=[Step(step_id=1, function=func_name, filters=filters)])

    # Último recurso
    return Plan(steps=[Step(step_id=1, function="get_cabecera", filters=[])])
