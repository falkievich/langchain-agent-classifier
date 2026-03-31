"""
tools/deterministic_router.py
─────────────────────────────
Router determinístico (fallback) para cuando el LLM falla.

Flujo:
  1. Normaliza el prompt del usuario.
  2. Calcula un score por cada función semántica usando keyword matching.
  3. Selecciona las N funciones con mayor score.
  4. Intenta extraer filtros del prompt.
  5. Devuelve un Plan determinístico listo para ejecutar.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from funcs.helpers_and_utility.langchain_utility import normalize_and_clean
from schema.call_and_plan_schema import Plan, Step, StepFilter
from schema.function_catalog import FUNCTION_CATALOG, FUNCTION_KEYWORDS


# ═══════════════════════════════════════════════════════════════
#  Configuración
# ═══════════════════════════════════════════════════════════════

MAX_FUNCTIONS_PER_QUERY = 4
MIN_SCORE_THRESHOLD = 0.3
KEYWORD_EXACT_BONUS = 3.0
KEYWORD_PARTIAL_BONUS = 1.5


# ═══════════════════════════════════════════════════════════════
#  Patrones directos (máxima certeza, sin scoring)
# ═══════════════════════════════════════════════════════════════

DIRECT_PATTERNS: List[Tuple[str, str, List[Dict[str, str]]]] = [
    # (regex, function_name, filtros fijos)
    (r"(?:cual|que) (?:es )?(?:el )?cuij", "get_cabecera", []),
    (r"(?:cual|que) (?:es )?(?:el )?estado (?:del )?expediente", "get_cabecera", []),
    (r"(?:cual|que) (?:es )?(?:la )?etapa procesal", "get_cabecera", []),
    (r"(?:cual|que) (?:es )?(?:la )?prioridad", "get_cabecera", []),
    (r"(?:cual|que) (?:es )?(?:la )?caratula", "get_cabecera", []),
    (r"(?:informacion|datos).*expediente", "get_cabecera", []),
    (r"(?:cuando|fecha).*hecho", "get_causa", []),
    (r"(?:como|forma).*inicio.*causa", "get_causa", []),
    (r"organismo (?:de )?control", "get_organismo_control", []),
]


# ═══════════════════════════════════════════════════════════════
#  Extracción de filtros del prompt
# ═══════════════════════════════════════════════════════════════

# Roles procesales reconocibles
_ROLES = ["imputado", "victima", "actor", "demandado", "denunciante", "querellante", "testigo"]
_CARGOS = ["fiscal", "juez", "secretario"]
_TIPOS_DEFENSOR = ["defensor publico", "defensor privado"]
_CONTACTOS = ["celular", "telefono", "email"]

# Patrones de extracción
_DNI_RE = re.compile(r"\b(\d{7,8})\b")
_CUIL_RE = re.compile(r"\b(\d{2}[\-.]?\d{7,8}[\-.]?\d{1})\b")
_QUOTED_RE = re.compile(r'["\']([^"\']+)["\']')
_NAME_RE = re.compile(
    r"(?:llamad[oa]|nombre|apellido|persona|abogado|funcionario)\s+"
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)"
)


def _extract_filters_from_prompt(prompt: str, function_name: str) -> List[StepFilter]:
    """Intenta extraer filtros del prompt para la función dada."""
    prompt_lower = normalize_and_clean(prompt)
    filters = []
    meta = FUNCTION_CATALOG.get(function_name, {})
    available_filters = meta.get("filters", {})

    # 1. Filtro por rol procesal
    if "vinculos.descripcion_vinculo" in available_filters:
        for rol in _ROLES:
            if rol in prompt_lower:
                filters.append(StepFilter(
                    field="vinculos.descripcion_vinculo", op="contains", value=rol
                ))
                break

    # 2. Filtro por cargo (funcionarios)
    if "cargo" in available_filters:
        for cargo in _CARGOS:
            if cargo in prompt_lower:
                filters.append(StepFilter(
                    field="cargo", op="contains", value=cargo
                ))
                break

    # 3. Filtro por tipo de defensor
    if "vinculo_descripcion" in available_filters:
        for tipo in _TIPOS_DEFENSOR:
            if tipo in prompt_lower:
                filters.append(StepFilter(
                    field="vinculo_descripcion", op="contains", value=tipo
                ))
                break

    # 4. Filtro por tipo de contacto
    for contact_field in ["domicilios.digital_clase", "relacionados.domicilios.digital_clase"]:
        if contact_field in available_filters:
            for contacto in _CONTACTOS:
                if contacto in prompt_lower:
                    filters.append(StepFilter(
                        field=contact_field, op="contains", value=contacto.capitalize()
                    ))
                    break
            break

    # 5. Filtro por detenido
    if "es_detenido" in available_filters:
        if "detenido" in prompt_lower or "detenida" in prompt_lower or "preso" in prompt_lower:
            filters.append(StepFilter(field="es_detenido", op="eq", value="true"))

    # 6. Filtro por nombre (entre comillas o patrón)
    if "nombre" in available_filters or "nombre_completo" in available_filters:
        quoted = _QUOTED_RE.findall(prompt)
        if quoted:
            field = "nombre_completo" if "nombre_completo" in available_filters else "nombre"
            filters.append(StepFilter(field=field, op="contains", value=quoted[0]))
        else:
            m = _NAME_RE.search(prompt)
            if m:
                field = "nombre_completo" if "nombre_completo" in available_filters else "nombre"
                filters.append(StepFilter(field=field, op="contains", value=m.group(1).strip()))

    # 7. Filtro por DNI
    if "numero_documento" in available_filters:
        m = _DNI_RE.search(prompt)
        if m:
            filters.append(StepFilter(field="numero_documento", op="eq", value=m.group(1)))

    return filters


# ═══════════════════════════════════════════════════════════════
#  Scoring de funciones
# ═══════════════════════════════════════════════════════════════

def _score_function(prompt_norm: str, prompt_tokens: set, func_name: str) -> float:
    """Calcula el score de relevancia de una función para el prompt dado."""
    keywords = FUNCTION_KEYWORDS.get(func_name, [])
    score = 0.0

    for kw in keywords:
        kw_norm = normalize_and_clean(kw)
        if kw_norm in prompt_norm:
            score += KEYWORD_EXACT_BONUS
        else:
            kw_tokens = set(kw_norm.split())
            overlap = kw_tokens & prompt_tokens
            if overlap:
                score += KEYWORD_PARTIAL_BONUS * (len(overlap) / len(kw_tokens))

    # Bonus por descripción
    desc = FUNCTION_CATALOG.get(func_name, {}).get("description", "")
    desc_norm = normalize_and_clean(desc)
    desc_tokens = set(desc_norm.split())
    overlap = prompt_tokens & desc_tokens
    if overlap:
        score += 0.5 * (len(overlap) / max(len(desc_tokens), 1))

    return score


# ═══════════════════════════════════════════════════════════════
#  Router principal
# ═══════════════════════════════════════════════════════════════

def route_query(user_prompt: str, max_functions: int = MAX_FUNCTIONS_PER_QUERY) -> Plan:
    """
    Dado un prompt, devuelve un Plan determinístico con funciones semánticas.
    Usado como fallback cuando el LLM falla.
    """
    prompt_norm = normalize_and_clean(user_prompt)
    prompt_tokens = set(prompt_norm.split())

    # 1. Patrones directos
    for pattern, func_name, fixed_filters in DIRECT_PATTERNS:
        m = re.search(pattern, prompt_norm)
        if m:
            filters = [StepFilter(**f) for f in fixed_filters] if fixed_filters else []
            if not filters:
                filters = _extract_filters_from_prompt(user_prompt, func_name)
            return Plan(steps=[
                Step(step_id=1, function=func_name, filters=filters)
            ])

    # 2. Scoring general
    scored: List[Tuple[float, str]] = []
    for func_name in FUNCTION_CATALOG:
        s = _score_function(prompt_norm, prompt_tokens, func_name)
        if s >= MIN_SCORE_THRESHOLD:
            scored.append((s, func_name))

    scored.sort(key=lambda x: x[0], reverse=True)

    # 3. Construir steps
    steps = []
    for i, (score, func_name) in enumerate(scored[:max_functions]):
        filters = _extract_filters_from_prompt(user_prompt, func_name)
        steps.append(Step(
            step_id=i + 1,
            function=func_name,
            filters=filters,
        ))

    # 4. Fallback a cabecera
    if not steps:
        steps.append(Step(step_id=1, function="get_cabecera", filters=[]))

    return Plan(steps=steps)
