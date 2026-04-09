"""
funcs/helpers_and_utility/query_string_to_params.py
────────────────────────────────────────────────────
Traduce el campo `query_string` generado por `_build_query_string` a un
string de query params compatible con URL (formato Postman / HTTP GET).

FORMATO DE SALIDA — simple y legible:
  ?field=value1,value2&other.field=value3

Reglas de traducción:
  • Todas las condiciones se aplanan: se ignoran los wrappers semánticos
    (SAME_ENTITY, AND, OR, NOT) y solo se conservan los pares campo=valor.
  • Si el mismo campo aparece varias veces con valores distintos → se
    combinan en una lista separada por comas: field=val1,val2
  • Condiciones dentro de NOT(...) o NOT cond → el campo lleva el prefijo
    "not." para indicar exclusión: not.field=value
  • Operadores:
      contains  →  field=value           (búsqueda parcial, sin sufijo)
      eq (=)    →  field=value
      >=        →  field__gte=value
      <=        →  field__lte=value
      !=        →  field__neq=value

Ejemplos:
  SAME_ENTITY(personas.nombre contains Manuel AND personas.rol contains actor)
  AND SAME_ENTITY(personas.nombre contains Thiago AND personas.rol contains demandado)
  AND materia.descripcion contains explotacion laboral
  AND cabecera.etapa contains prueba
  →
  ?personas.nombre=Manuel,Thiago&personas.rol=actor,demandado
  &materia.descripcion=explotacion laboral&cabecera.etapa=prueba

  NOT(personas.es_detenido=false) AND personas.rol contains imputado
  →
  ?not.personas.es_detenido=false&personas.rol=imputado

  (personas.rol contains victima OR personas.rol contains querellante)
  →
  ?personas.rol=victima,querellante
"""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════
#  Utilidades de parseo
# ═══════════════════════════════════════════════════════════════

def _find_balanced_paren(s: str, start: int) -> int:
    """Devuelve el índice del ')' de cierre que balancea el '(' en `start`."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"Paréntesis no balanceados en: {s!r}")


# Regex para parsear una condición atómica:  field OP value
_CONDITION_RE = re.compile(
    r"^(?P<field>[^\s=!<>]+)"
    r"\s*"
    r"(?P<op>contains|>=|<=|!=|=)"
    r"\s*"
    r"(?P<value>.+)$",
    re.IGNORECASE,
)

_AND_OR_SPLIT_RE = re.compile(r"\s+(?:AND|OR)\s+", re.IGNORECASE)


def _parse_condition(raw: str) -> Tuple[str, str] | None:
    """
    Convierte "field OP value" → (param_key, value).

    Tabla de operadores → sufijo en el param_key:
      contains, =  →  ""           (field=value)
      >=           →  "__gte"      (field__gte=value)
      <=           →  "__lte"      (field__lte=value)
      !=           →  "__neq"      (field__neq=value)

    Devuelve None si no se pudo parsear.
    """
    raw = raw.strip()
    m = _CONDITION_RE.match(raw)
    if not m:
        return None

    field  = m.group("field").strip()
    op     = m.group("op").strip().lower()
    value  = m.group("value").strip()

    suffix = {"contains": "", "=": "", ">=": "__gte", "<=": "__lte", "!=": "__neq"}.get(op, "")
    return (f"{field}{suffix}", value)


def _split_inner(inner: str) -> List[str]:
    """Divide el contenido de un grupo por AND/OR y devuelve las partes."""
    return [p.strip() for p in _AND_OR_SPLIT_RE.split(inner) if p.strip()]


# ═══════════════════════════════════════════════════════════════
#  Extractor de condiciones atómicas desde query_string
# ═══════════════════════════════════════════════════════════════

def _extract_conditions(qs: str) -> List[Tuple[str, str, bool]]:
    """
    Recorre `qs` y extrae TODAS las condiciones atómicas como:
        (param_key, value, is_negated)

    Ignora los wrappers semánticos (SAME_ENTITY, NOT, grupos OR/AND):
    solo importan los pares campo=valor que contienen.

    is_negated = True  →  condición dentro de NOT(...) o NOT cond_suelta.
    is_negated = False →  el resto.
    """
    conditions: List[Tuple[str, str, bool]] = []
    i = 0
    n = len(qs)

    while i < n:
        # ── Saltar espacios ──────────────────────────────────────
        m_ws = re.match(r"^\s+", qs[i:])
        if m_ws:
            i += m_ws.end()
            continue

        # ── Separadores AND/OR de nivel raíz ────────────────────
        m_sep = re.match(r"^(?:AND|OR)\s+", qs[i:], re.IGNORECASE)
        if m_sep:
            i += m_sep.end()
            continue

        # ── NOT SAME_ENTITY(...) ─────────────────────────────────
        m = re.match(r"^NOT\s+SAME_ENTITY\s*\(", qs[i:], re.IGNORECASE)
        if m:
            paren_start = i + m.end() - 1
            paren_end   = _find_balanced_paren(qs, paren_start)
            inner       = qs[paren_start + 1: paren_end]
            for part in _split_inner(inner):
                parsed = _parse_condition(part)
                if parsed:
                    conditions.append((*parsed, True))
            i = paren_end + 1
            continue

        # ── SAME_ENTITY(...) ─────────────────────────────────────
        m = re.match(r"^SAME_ENTITY\s*\(", qs[i:], re.IGNORECASE)
        if m:
            paren_start = i + m.end() - 1
            paren_end   = _find_balanced_paren(qs, paren_start)
            inner       = qs[paren_start + 1: paren_end]
            for part in _split_inner(inner):
                parsed = _parse_condition(part)
                if parsed:
                    conditions.append((*parsed, False))
            i = paren_end + 1
            continue

        # ── NOT(...) ─────────────────────────────────────────────
        m = re.match(r"^NOT\s*\(", qs[i:], re.IGNORECASE)
        if m:
            paren_start = i + m.end() - 1
            paren_end   = _find_balanced_paren(qs, paren_start)
            inner       = qs[paren_start + 1: paren_end]
            for part in _split_inner(inner):
                parsed = _parse_condition(part)
                if parsed:
                    conditions.append((*parsed, True))
            i = paren_end + 1
            continue

        # ── NOT cond_suelta (sin paréntesis) ─────────────────────
        m = re.match(
            r"^NOT\s+(?P<rest>[^\s(][^\n]*?)(?=\s+(?:AND|OR)\s+|$)",
            qs[i:],
            re.IGNORECASE,
        )
        if m:
            parsed = _parse_condition(m.group("rest").strip())
            if parsed:
                conditions.append((*parsed, True))
            i += m.end()
            continue

        # ── Grupo entre paréntesis (OR / AND sin prefijo) ────────
        if qs[i] == "(":
            paren_end  = _find_balanced_paren(qs, i)
            inner      = qs[i + 1: paren_end]
            for part in _split_inner(inner):
                parsed = _parse_condition(part)
                if parsed:
                    conditions.append((*parsed, False))
            i = paren_end + 1
            continue

        # ── Condición suelta ──────────────────────────────────────
        # Avanzar hasta el próximo AND/OR de nivel raíz
        depth = 0
        j = i
        while j < n:
            if qs[j] == "(":
                depth += 1
            elif qs[j] == ")":
                depth -= 1
            elif depth == 0 and re.match(r"^\s+(?:AND|OR)\s+", qs[j:], re.IGNORECASE):
                break
            j += 1

        chunk = qs[i:j].strip()
        if chunk:
            parsed = _parse_condition(chunk)
            if parsed:
                conditions.append((*parsed, False))
        i = j

    return conditions


# ═══════════════════════════════════════════════════════════════
#  Construcción del query_params string
# ═══════════════════════════════════════════════════════════════

def build_query_params(query_string: str) -> str:
    """
    Convierte `query_string` a un string de query params Postman-ready.

    Agrupa múltiples valores del mismo campo con comas:
        field=val1,val2

    Condiciones negadas llevan prefijo "not.":
        not.field=value

    Args:
        query_string: La query lógica con SAME_ENTITY, AND, OR, NOT, etc.

    Returns:
        String tipo "?key=val1,val2&key2=val3" o "" si no hay condiciones.

    Ejemplos
    --------
    >>> qs = (
    ...     "SAME_ENTITY(personas_legajo.nombre_completo contains Manuel "
    ...     "AND personas_legajo.vinculos.descripcion_vinculo contains actor) "
    ...     "AND SAME_ENTITY(personas_legajo.nombre_completo contains Thiago "
    ...     "AND personas_legajo.vinculos.descripcion_vinculo contains demandado) "
    ...     "AND materia_delitos.descripcion contains explotacion laboral "
    ...     "AND cabecera_legajo.etapa_procesal_descripcion contains prueba"
    ... )
    >>> build_query_params(qs)
    '?personas_legajo.nombre_completo=Manuel,Thiago&personas_legajo.vinculos.descripcion_vinculo=actor,demandado&materia_delitos.descripcion=explotacion laboral&cabecera_legajo.etapa_procesal_descripcion=prueba'
    """
    if not query_string or not query_string.strip():
        return ""

    raw_conditions = _extract_conditions(query_string.strip())
    if not raw_conditions:
        return ""

    # Acumular valores por param_key, manteniendo orden de aparición.
    # Separamos negados (not.key) de normales (key).
    # Usamos OrderedDict para preservar el orden de primera aparición.
    grouped: OrderedDict[str, List[str]] = OrderedDict()

    for param_key, value, negated in raw_conditions:
        full_key = f"not.{param_key}" if negated else param_key
        if full_key not in grouped:
            grouped[full_key] = []
        # Evitar duplicar el mismo valor para el mismo campo
        if value not in grouped[full_key]:
            grouped[full_key].append(value)

    params = [f"{k}={','.join(v)}" for k, v in grouped.items()]

    if not params:
        return ""

    return "?" + "&".join(params)


# ═══════════════════════════════════════════════════════════════
#  Integración con el resultado de execute_plan
# ═══════════════════════════════════════════════════════════════

def enrich_result_with_query_params(result: dict) -> dict:
    """
    Recibe el dict resultado de `execute_plan` (que ya tiene `query_string`)
    y le agrega `query_params` inmediatamente debajo, sin modificar nada más.
    """
    query_string = result.get("query_string", "")
    query_params = build_query_params(query_string)

    new_result: dict = {}
    for k, v in result.items():
        new_result[k] = v
        if k == "query_string":
            new_result["query_params"] = query_params

    if "query_params" not in new_result:
        new_result["query_params"] = query_params

    return new_result


# ═══════════════════════════════════════════════════════════════
#  CLI de prueba rápida
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    _EXAMPLES = [
        (
            "Ejemplo 1 — Manuel (actor) + Thiago (demandado) + delito + etapa",
            (
                "SAME_ENTITY(personas_legajo.nombre_completo contains Manuel "
                "AND personas_legajo.vinculos.descripcion_vinculo contains actor) "
                "AND SAME_ENTITY(personas_legajo.nombre_completo contains Thiago "
                "AND personas_legajo.vinculos.descripcion_vinculo contains demandado) "
                "AND materia_delitos.descripcion contains explotacion laboral "
                "AND cabecera_legajo.etapa_procesal_descripcion contains prueba"
            ),
            (
                "?personas_legajo.nombre_completo=Manuel,Thiago"
                "&personas_legajo.vinculos.descripcion_vinculo=actor,demandado"
                "&materia_delitos.descripcion=explotacion laboral"
                "&cabecera_legajo.etapa_procesal_descripcion=prueba"
            ),
        ),
        (
            "Ejemplo 2 — Filtros sueltos eq y contains",
            (
                "personas_legajo.vinculos.descripcion_vinculo contains victima "
                "AND cabecera_legajo.estado_expediente_descripcion=En tramite"
            ),
            (
                "?personas_legajo.vinculos.descripcion_vinculo=victima"
                "&cabecera_legajo.estado_expediente_descripcion=En tramite"
            ),
        ),
        (
            "Ejemplo 3 — NOT(group)",
            (
                "NOT(personas_legajo.es_detenido=false) "
                "AND personas_legajo.vinculos.descripcion_vinculo contains imputado"
            ),
            (
                "?not.personas_legajo.es_detenido=false"
                "&personas_legajo.vinculos.descripcion_vinculo=imputado"
            ),
        ),
        (
            "Ejemplo 4 — Operadores gte / lte",
            (
                "radicaciones.fecha_desde>=2023-01-01 "
                "AND radicaciones.fecha_hasta<=2024-12-31"
            ),
            (
                "?radicaciones.fecha_desde__gte=2023-01-01"
                "&radicaciones.fecha_hasta__lte=2024-12-31"
            ),
        ),
        (
            "Ejemplo 5 — NOT SAME_ENTITY",
            (
                "NOT SAME_ENTITY(personas_legajo.vinculos.descripcion_vinculo contains imputado "
                "AND personas_legajo.es_detenido=false) "
                "AND cabecera_legajo.etapa_procesal_descripcion contains prueba"
            ),
            (
                "?not.personas_legajo.vinculos.descripcion_vinculo=imputado"
                "&not.personas_legajo.es_detenido=false"
                "&cabecera_legajo.etapa_procesal_descripcion=prueba"
            ),
        ),
        (
            "Ejemplo 6 — Grupo OR (víctima o querellante)",
            (
                "(personas_legajo.vinculos.descripcion_vinculo contains victima "
                "OR personas_legajo.vinculos.descripcion_vinculo contains querellante) "
                "AND cabecera_legajo.estado_expediente_descripcion contains tramite"
            ),
            (
                "?personas_legajo.vinculos.descripcion_vinculo=victima,querellante"
                "&cabecera_legajo.estado_expediente_descripcion=tramite"
            ),
        ),
        (
            "Ejemplo 7 — Sistemas múltiples con personas (OR)",
            (
                "personas_legajo.nombre_completo contains Thiago "
                "AND personas_legajo.nombre_completo contains Jose "
                "AND (_root.codigo_sistema=iurixweb OR _root.codigo_sistema=criminis)"
            ),
            (
                "?personas_legajo.nombre_completo=Thiago,Jose"
                "&_root.codigo_sistema=iurixweb,criminis"
            ),
        ),
        (
            "Ejemplo 8 — neq operator",
            "personas_legajo.genero!=MASCULINO AND cabecera_legajo.prioridad!=BAJO",
            (
                "?personas_legajo.genero__neq=MASCULINO"
                "&cabecera_legajo.prioridad__neq=BAJO"
            ),
        ),
    ]

    all_passed = True
    for title, qs, expected in _EXAMPLES:
        result  = build_query_params(qs)
        status  = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"\n{'─' * 70}")
        print(f"  {status} {title}")
        print(f"  query_string : {qs}")
        print(f"  esperado     : {expected}")
        if result != expected:
            print(f"  obtenido     : {result}")

    print(f"\n{'═' * 70}")
    print(f"  {'✅ Todos los ejemplos OK' if all_passed else '❌ Hay diferencias'}")
