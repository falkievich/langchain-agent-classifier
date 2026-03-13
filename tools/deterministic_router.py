"""
tools/deterministic_router.py
─────────────────────────────
Router determinístico que convierte la pregunta del usuario
en una lista de funciones extractoras concretas SIN depender del LLM.

Flujo:
  1. Normaliza el prompt del usuario.
  2. Calcula un score por cada ToolEntry del registry usando keyword matching.
  3. Selecciona las N herramientas con mayor score (top-K).
  4. Devuelve un Plan determinístico listo para ejecutar.

Esto elimina la variabilidad del Planner basado en LLM.
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

from funcs.helpers_and_utility.langchain_utility import normalize_and_clean
from extractors.registry import TOOL_REGISTRY, TOOL_BY_NAME, ToolEntry
from schema.call_and_plan_schema import Plan, Call

# ═══════════════════════════════════════════════════════════════
#  Configuración
# ═══════════════════════════════════════════════════════════════

MAX_TOOLS_PER_QUERY = 8          # máximo de tools a ejecutar por consulta
MIN_SCORE_THRESHOLD = 0.15       # score mínimo para considerar una tool
KEYWORD_EXACT_BONUS = 3.0        # bonus cuando keyword aparece completo en el prompt
KEYWORD_PARTIAL_BONUS = 1.5      # bonus cuando keyword es subcadena
DESCRIPTION_MATCH_BONUS = 0.8    # bonus por coincidencia en la descripción
SECTION_BONUS = 1.0              # bonus extra si la sección general matchea
SECTION_HINT_BONUS = 4.0         # bonus cuando el condition extractor sugiere la sección
DATA_FIELD_HINT_BONUS = 2.5      # bonus cuando el condition extractor sugiere un data_field


# ═══════════════════════════════════════════════════════════════
#  Sección → palabras clave de la sección
# ═══════════════════════════════════════════════════════════════

SECTION_KEYWORDS = {
    "cabecera_legajo": ["expediente", "cabecera", "legajo", "cuij", "estado", "tipo proceso",
                        "etapa", "prioridad", "caratula", "organismo", "secretaria",
                        "ubicacion", "fecha inicio", "fecha modificacion", "usuario"],
    "personas_legajo": ["persona", "personas", "imputado", "victima", "actor", "demandado",
                        "detenido", "vinculo", "caracteristica", "relacionado", "domicilio persona",
                        "menor", "ocupacion", "estado civil", "calificacion legal",
                        "dni persona", "cuil persona", "nacimiento persona"],
    "abogados_legajo": ["abogado", "abogados", "defensor", "matricula", "representado",
                        "cliente", "defensor publico", "defensor privado",
                        "domicilio abogado", "a quien representa"],
    "funcionarios":    ["funcionario", "funcionarios", "fiscal", "juez", "cargo",
                        "email funcionario"],
    "causa":           ["causa", "hecho", "forma inicio", "fecha hecho",
                        "caratula causa"],
    "dependencias_vistas": ["dependencia", "dependencias", "organismo dependencia",
                            "jerarquia", "tipo dependencia", "activo dependencia"],
    "radicaciones":    ["radicacion", "radicaciones", "movimiento", "motivo radicacion"],
    "materia_delitos": ["delito", "delitos", "materia", "codigo delito"],
    "extras":          ["clasificador", "clasificacion", "organismo control", "sistema",
                        "entidad", "seguridad", "clave causa", "estado legajo"],
}


# ═══════════════════════════════════════════════════════════════
#  Patrones especiales: regex → tool name directo
#  (Para casos muy comunes que queremos resolver 100% deterministico)
# ═══════════════════════════════════════════════════════════════

DIRECT_PATTERNS: List[Tuple[str, str, Optional[int]]] = [
    # (regex, tool_name, grupo del regex para extraer argumento o None)
    (r"(?:cual|que) (?:es )?(?:el )?cuij", "obtener_cuij", None),
    (r"(?:cual|que) (?:es )?(?:el )?estado (?:del )?expediente", "obtener_estado_expediente_descripcion", None),
    (r"(?:cual|que) (?:es )?(?:la )?etapa procesal", "obtener_etapa_procesal_descripcion", None),
    (r"(?:cual|que) (?:es )?(?:el )?tipo (?:de )?proceso", "obtener_tipo_proceso", None),
    (r"(?:cual|que) (?:es )?(?:la )?prioridad", "obtener_prioridad", None),
    (r"(?:cual|que) (?:es )?(?:la )?caratula publica", "obtener_caratula_publica", None),
    (r"(?:cuando|fecha).*inicio", "obtener_fecha_inicio", None),
    (r"(?:cuando|fecha).*modificacion", "obtener_fecha_modificacion", None),
    (r"(?:cuando|fecha).*hecho", "obtener_causa_fecha_hecho", None),
    (r"(?:como|forma).*inicio.*causa", "obtener_causa_forma_inicio", None),
    (r"(?:todos|todas|listar|listado|lista).*persona", "listar_personas", None),
    (r"(?:todos|todas|listar|listado|lista).*abogado", "listar_abogados", None),
    (r"(?:todos|todas|listar|listado|lista).*funcionario", "listar_funcionarios", None),
    (r"(?:todos|todas|listar|listado|lista).*dependencia", "listar_dependencias", None),
    (r"(?:todos|todas|listar|listado|lista).*radicacion", "listar_radicaciones", None),
    (r"(?:todos|todas|listar|listado|lista).*delito", "listar_delitos", None),
    (r"(?:todos|todas|listar|listado|lista).*clasificador", "listar_clasificadores_legajo", None),
    (r"organismo (?:de )?control", "obtener_organismo_control", None),
    (r"persona.*detenid[oa]", "buscar_persona_por_estado_detencion", None),
    (r"(?:quien|quienes).*detenid[oa]", "buscar_persona_por_estado_detencion", None),
    (r"(?:hay|existe).*menor", "buscar_persona_por_es_menor", None),
]


# ═══════════════════════════════════════════════════════════════
#  Extracción de argumentos del prompt
# ═══════════════════════════════════════════════════════════════

# Patrones para detectar valores explícitos en el prompt
_DNI_RE = re.compile(r"\b(\d{7,8})\b")
_CUIL_RE = re.compile(r"\b(\d{2}[\-.]?\d{7,8}[\-.]?\d{1})\b")
_DATE_RE = re.compile(r"\b(\d{4}[\-/]\d{2}[\-/]\d{2})\b")
_QUOTED_RE = re.compile(r'["\']([^"\']+)["\']')
_NAME_RE = re.compile(r"(?:llamad[oa]|nombre|apellido|persona|abogado|funcionario)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)")


def extract_argument(prompt: str, tool: ToolEntry) -> Optional[str]:
    """
    Intenta extraer del prompt el argumento que necesita la tool.
    Si no puede, devuelve None.
    """
    if tool.args == 0:
        return None

    # 1. Valores entre comillas — más explícito
    quoted = _QUOTED_RE.findall(prompt)
    if quoted:
        return quoted[0]

    prompt_lower = prompt.lower()

    # 2. Si la tool busca por DNI
    if "dni" in tool.name or "documento" in tool.name:
        m = _DNI_RE.search(prompt)
        if m:
            return m.group(1)

    # 3. Si la tool busca por CUIL
    if "cuil" in tool.name:
        m = _CUIL_RE.search(prompt)
        if m:
            return m.group(1).replace("-", "").replace(".", "")

    # 4. Si la tool busca por fecha
    if "fecha" in tool.name:
        m = _DATE_RE.search(prompt)
        if m:
            return m.group(1).replace("/", "-")

    # 5. Si busca booleano
    if "detencion" in tool.name or "menor" in tool.name or "activo" in tool.name:
        for w in ["si", "sí", "true", "detenido", "detenida", "menor", "activa", "activo"]:
            if w in prompt_lower:
                return "true"
        for w in ["no", "false", "libre", "mayor", "inactiva", "inactivo"]:
            if w in prompt_lower:
                return "false"
        return "true"  # default si pregunta "hay detenidos?"

    # 6. Si busca por nombre — intentar capturar
    if "nombre" in tool.name or "cliente" in tool.name:
        m = _NAME_RE.search(prompt)
        if m:
            return m.group(1).strip()

    # 7. Si busca por rol
    if "rol" in tool.name:
        roles = ["imputado", "victima", "actor", "demandado", "denunciante",
                 "querellante", "testigo", "perito"]
        for r in roles:
            if r in prompt_lower:
                return r

    # 8. Si busca por genero
    if "genero" in tool.name:
        if "masculino" in prompt_lower or "hombre" in prompt_lower or "varon" in prompt_lower:
            return "MASCULINO"
        if "femenino" in prompt_lower or "mujer" in prompt_lower:
            return "FEMENINO"

    # 9. Fallback: tomar la parte del prompt después de un ":" o última palabra significativa
    # No podemos determinar el argumento de forma determinística
    return None


# ═══════════════════════════════════════════════════════════════
#  Scoring de tools
# ═══════════════════════════════════════════════════════════════

def _score_tool(prompt_norm: str, prompt_tokens: set, tool: ToolEntry) -> float:
    """Calcula el score de relevancia de una tool para el prompt dado."""
    score = 0.0

    # 1. Keyword matching
    for kw in tool.keywords:
        kw_norm = normalize_and_clean(kw)
        if kw_norm in prompt_norm:
            score += KEYWORD_EXACT_BONUS
        else:
            # Coincidencia parcial: ¿algún token del keyword está en el prompt?
            kw_tokens = set(kw_norm.split())
            overlap = kw_tokens & prompt_tokens
            if overlap:
                score += KEYWORD_PARTIAL_BONUS * (len(overlap) / len(kw_tokens))

    # 2. Descripción matching (parcial)
    desc_norm = normalize_and_clean(tool.description)
    desc_tokens = set(desc_norm.split())
    overlap = prompt_tokens & desc_tokens
    if overlap:
        score += DESCRIPTION_MATCH_BONUS * (len(overlap) / max(len(desc_tokens), 1))

    # 3. Bonus de sección
    section_kws = SECTION_KEYWORDS.get(tool.section, [])
    for skw in section_kws:
        if normalize_and_clean(skw) in prompt_norm:
            score += SECTION_BONUS
            break

    return score


# ═══════════════════════════════════════════════════════════════
#  Router principal
# ═══════════════════════════════════════════════════════════════

def route_query(
    user_prompt: str,
    max_tools: int = MAX_TOOLS_PER_QUERY,
    hint_sections: Optional[List[str]] = None,
    hint_data_fields: Optional[List[str]] = None,
) -> Plan:
    """
    Dado un prompt de usuario, devuelve un Plan determinístico con las
    tools más relevantes y sus argumentos extraídos.
    
    Args:
        user_prompt: consulta del usuario.
        max_tools: máximo de tools a incluir.
        hint_sections: secciones sugeridas por el condition extractor (opcional).
            Si se proporcionan, se da prioridad a tools de esas secciones.
        hint_data_fields: campos sugeridos por el condition extractor (opcional).
            Ayuda a refinar qué tools seleccionar (ej: "domicilios" → listar_domicilios_*).
    """
    prompt_norm = normalize_and_clean(user_prompt)
    prompt_tokens = set(prompt_norm.split())

    # 1. Verificar patrones directos (máxima determinismo)
    direct_calls: List[Call] = []
    for pattern, tool_name, arg_group in DIRECT_PATTERNS:
        m = re.search(pattern, prompt_norm)
        if m:
            tool = TOOL_BY_NAME.get(tool_name)
            if tool:
                args = []
                if tool.args > 0:
                    extracted = extract_argument(user_prompt, tool)
                    if extracted:
                        args = [extracted]
                    else:
                        continue  # no tenemos argumento → no agregar
                direct_calls.append(Call(tool=tool_name, args=args))

    if direct_calls and not hint_sections:
        # Si hay matches directos y no tenemos hints del LLM, usarlos
        return Plan(calls=direct_calls[:max_tools])

    # 2. Scoring general
    scored: List[Tuple[float, ToolEntry]] = []
    for tool in TOOL_REGISTRY:
        s = _score_tool(prompt_norm, prompt_tokens, tool)

        # Bonus por secciones sugeridas por el condition extractor
        if hint_sections and tool.section in hint_sections:
            s += SECTION_HINT_BONUS

        # Bonus por data_fields sugeridos
        if hint_data_fields and hint_data_fields != ["*"]:
            for df in hint_data_fields:
                df_norm = normalize_and_clean(df)
                if df_norm in tool.name or df_norm in normalize_and_clean(tool.description):
                    s += DATA_FIELD_HINT_BONUS
                    break

        if s >= MIN_SCORE_THRESHOLD:
            scored.append((s, tool))

    # Ordenar por score descendente
    scored.sort(key=lambda x: x[0], reverse=True)

    # 3. Construir calls
    calls: List[Call] = []
    for score, tool in scored[:max_tools]:
        args = []
        if tool.args > 0:
            extracted = extract_argument(user_prompt, tool)
            if extracted is not None:
                args = [extracted]
            else:
                # Tool con argumento requerido pero no pudimos extraerlo.
                # Solo incluir si es una tool de listado (sin args)
                continue
        calls.append(Call(tool=tool.name, args=args))

    # También incluir direct_calls que no estén duplicados
    existing_tools = {c.tool for c in calls}
    for dc in direct_calls:
        if dc.tool not in existing_tools:
            calls.append(dc)

    # 4. Si no hay matches, fallback a cabecera completa
    if not calls:
        calls.append(Call(tool="obtener_cabecera_legajo", args=[]))

    return Plan(calls=calls[:max_tools])


def route_query_with_hints(
    user_prompt: str,
    hint_sections: Optional[List[str]] = None,
    hint_data_fields: Optional[List[str]] = None,
    max_tools: int = MAX_TOOLS_PER_QUERY,
) -> Plan:
    """
    Routing determinístico enriquecido con hints del condition extractor.
    Usa hints para mejorar la selección, pero NO depende del LLM para planificar.
    """
    return route_query(
        user_prompt,
        max_tools=max_tools,
        hint_sections=hint_sections,
        hint_data_fields=hint_data_fields,
    )
