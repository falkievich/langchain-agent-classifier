import unicodedata
from typing import Any, List

from schema.plan_schema import (
    Condicion,
    ConsultaAnidada,
    OperadorCondicion,
    PasoConsulta,
    Plan,
)

# -------- Normalizer --------
# Traduce los conceptos semánticos del Plan (producido por el Intérprete)
# a condiciones concretas con paths y valores reales del JSON.
#
# Responsabilidades:
#   1. Resolver "concept" → Condicion con path + op + value reales del JSON
#   2. Normalizar valores directos (tildes, mayúsculas, género, plural)
#      para que siempre coincidan con los valores reales del JSON
#
# 100% código. Sin LLM.
# El Searcher recibe un Plan ya normalizado y nunca ve conceptos semánticos.


# ────────────────────────────────────────────────────────────────────────────
# 1. Utilidad: normalizar texto
# ────────────────────────────────────────────────────────────────────────────

def _limpiar(texto: str) -> str:
    """
    Convierte a minúsculas, elimina tildes y espacios extra.
    Ejemplos:
        "Víctima"   → "victima"
        "IMPUTADO"  → "imputado"
        "acusada"   → "acusada"
    """
    if not isinstance(texto, str):
        return texto
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


# ────────────────────────────────────────────────────────────────────────────
# 2. Diccionario de sinónimos por campo
#    Clave:   valor normalizado (sin tildes, minúsculas)
#    Valor:   valor real en el JSON
#
#    Cubre: género (imputado/imputada), número (víctimas/víctima),
#           tildes (víctima/victima), sinónimos jurídicos (acusado → imputado)
# ────────────────────────────────────────────────────────────────────────────

SINONIMOS_ROL: dict[str, str] = {
    # imputado
    "imputado":     "imputado",
    "imputada":     "imputado",
    "imputados":    "imputado",
    "imputadas":    "imputado",
    "acusado":      "imputado",
    "acusada":      "imputado",
    "acusados":     "imputado",
    "acusadas":     "imputado",
    "procesado":    "imputado",
    "procesada":    "imputado",
    "inculpado":    "imputado",
    "inculpada":    "imputado",
    # victima
    "victima":      "victima",
    "victimas":     "victima",
    "damnificado":  "victima",
    "damnificada":  "victima",
    "damnificados": "victima",
    "damnificadas": "victima",
    "ofendido":     "victima",
    "ofendida":     "victima",
    # representante legal no letrado
    "representante legal no letrado": "representante legal no letrado",
    "representante legal":            "representante legal no letrado",
    "representante":                  "representante legal no letrado",
    "tutor":                          "representante legal no letrado",
    "tutora":                         "representante legal no letrado",
}

SINONIMOS_VINCULO_CODIGO: dict[str, list[str]] = {
    # defensor privado
    "defensor privado":  ["DPRIV"],
    "defensora privada": ["DPRIV"],
    "defensor":          ["DPRIV", "DPUB"],
    "defensora":         ["DPRIV", "DPUB"],
    "defensor publico":  ["DPUB"],
    "defensora publica": ["DPUB"],
    # querellante
    "querellante":       ["QUER"],
    "querellantes":      ["QUER"],
    # patrocinante
    "patrocinante":      ["PAT"],
    "abogado patron":    ["PAT"],
}

SINONIMOS_DIGITAL_CLASE_CODIGO: dict[str, str] = {
    "celular":    "CEL",
    "cel":        "CEL",
    "movil":      "CEL",
    "telefono":   "CEL",
    "teléfono":   "CEL",
    "email":      "MAIL",
    "correo":     "MAIL",
    "mail":       "MAIL",
    "electronico":"MAIL",
    "electrónico":"MAIL",
}

SINONIMOS_CARGO_FUNCIONARIO: dict[str, str] = {
    # fiscal
    "fiscal":                    "Fiscal de investigacion",
    "fiscal de investigacion":   "Fiscal de investigacion",
    "fiscal de investigación":   "Fiscal de investigacion",
    # juez
    "juez":                      "Juez",
    "jueza":                     "Juez",
    # defensor publico (funcionario)
    "defensor publico oficial":  "Defensor Público Oficial",
}


def _normalizar_valor_por_path(path: str, valor: Any) -> Any:
    """
    Normaliza un valor según el path al que pertenece.
    Usa los diccionarios de sinónimos para devolver el valor real del JSON.
    Si no encuentra sinónimo, devuelve el valor limpio.
    """
    if not isinstance(valor, str):
        return valor

    valor_limpio = _limpiar(valor)

    if path in ("rol",):
        return SINONIMOS_ROL.get(valor_limpio, valor_limpio)

    if path in ("vinculo_codigo",):
        # devuelve lista para operador IN
        return SINONIMOS_VINCULO_CODIGO.get(valor_limpio, [valor_limpio])

    if path in ("digital_clase_codigo",):
        return SINONIMOS_DIGITAL_CLASE_CODIGO.get(valor_limpio, valor_limpio.upper())

    if path in ("cargo",):
        return SINONIMOS_CARGO_FUNCIONARIO.get(valor_limpio, valor)

    return valor_limpio


# ────────────────────────────────────────────────────────────────────────────
# 3. Diccionario de conceptos semánticos
#    Cada concepto se resuelve a una Condicion concreta con valores reales.
# ────────────────────────────────────────────────────────────────────────────

def _resolver_concepto(concept: str) -> Condicion:
    """
    Traduce un concepto semántico a una Condicion con path + op + value reales.

    Raises:
        ValueError: Si el concepto no está registrado.
    """
    concept_upper = concept.strip().upper()

    CONCEPTOS: dict[str, Condicion] = {

        # ── Roles de personas ──────────────────────────────────────────────
        "ROLE.IMPUTADO": Condicion(
            path="rol",
            op=OperadorCondicion.CONTAINS,
            value="imputado",
        ),
        "ROLE.VICTIMA": Condicion(
            path="rol",
            op=OperadorCondicion.CONTAINS,
            value="victima",
        ),
        "ROLE.REPRESENTANTE": Condicion(
            path="rol",
            op=OperadorCondicion.CONTAINS,
            value="representante legal no letrado",
        ),

        # ── Vínculos de abogados ───────────────────────────────────────────
        # LAWYER.DEFENSOR cubre tanto defensor privado (DPRIV) como público (DPUB)
        "LAWYER.DEFENSOR": Condicion(
            path="vinculo_codigo",
            op=OperadorCondicion.IN,
            value=["DPRIV", "DPUB"],
        ),
        "LAWYER.DEFENSOR_PRIVADO": Condicion(
            path="vinculo_codigo",
            op=OperadorCondicion.EQ,
            value="DPRIV",
        ),
        "LAWYER.DEFENSOR_PUBLICO": Condicion(
            path="vinculo_codigo",
            op=OperadorCondicion.EQ,
            value="DPUB",
        ),
        "LAWYER.QUERELLANTE": Condicion(
            path="vinculo_codigo",
            op=OperadorCondicion.EQ,
            value="QUER",
        ),
        "LAWYER.PATROCINANTE": Condicion(
            path="vinculo_codigo",
            op=OperadorCondicion.EQ,
            value="PAT",
        ),

        # ── Contactos en domicilios ────────────────────────────────────────
        "CONTACT.CELULAR": Condicion(
            path="digital_clase_codigo",
            op=OperadorCondicion.EQ,
            value="CEL",
        ),
        "CONTACT.EMAIL": Condicion(
            path="digital_clase_codigo",
            op=OperadorCondicion.EQ,
            value="MAIL",
        ),

        # ── Cargos de funcionarios ─────────────────────────────────────────
        "FUNC.FISCAL": Condicion(
            path="cargo",
            op=OperadorCondicion.CONTAINS,
            value="Fiscal",
        ),
        "FUNC.JUEZ": Condicion(
            path="cargo",
            op=OperadorCondicion.CONTAINS,
            value="Juez",
        ),
        "FUNC.DEFENSOR_PUBLICO_OFICIAL": Condicion(
            path="cargo",
            op=OperadorCondicion.CONTAINS,
            value="Defensor",
        ),
    }

    if concept_upper not in CONCEPTOS:
        raise ValueError(
            f"Concepto semántico desconocido: '{concept}'.\n"
            f"Conceptos disponibles: {sorted(CONCEPTOS.keys())}"
        )

    return CONCEPTOS[concept_upper]


# ────────────────────────────────────────────────────────────────────────────
# 4. Normalización de condiciones individuales
# ────────────────────────────────────────────────────────────────────────────

def _normalizar_condicion(condicion: Condicion) -> Condicion:
    """
    Recibe una Condicion y devuelve una nueva Condicion normalizada:
      - Si tiene 'concept': la resuelve a path + op + value reales
      - Si tiene 'path' + 'value': normaliza el value según el path
      - Si tiene 'value_from': la deja intacta (es una referencia de PIPE)
    """
    # Caso 1: referencia cruzada de PIPE → no tocar
    if condicion.value_from is not None:
        return condicion

    # Caso 2: concepto semántico → resolver a valores reales
    if condicion.concept is not None:
        return _resolver_concepto(condicion.concept)

    # Caso 3: path + value directo → normalizar el value
    if condicion.path is not None and condicion.value is not None:
        valor_normalizado = _normalizar_valor_por_path(condicion.path, condicion.value)

        # Si la normalización devolvió una lista y el operador era EQ, cambiar a IN
        if isinstance(valor_normalizado, list) and condicion.op == OperadorCondicion.EQ:
            return Condicion(
                path=condicion.path,
                op=OperadorCondicion.IN,
                value=valor_normalizado,
            )

        return Condicion(
            path=condicion.path,
            op=condicion.op,
            value=valor_normalizado,
        )

    # Caso 4: condición incompleta → devolver sin cambios
    return condicion


def _normalizar_lista_condiciones(condiciones: List[Condicion]) -> List[Condicion]:
    return [_normalizar_condicion(c) for c in condiciones]


# ────────────────────────────────────────────────────────────────────────────
# 5. Normalización del Plan completo
# ────────────────────────────────────────────────────────────────────────────

def _normalizar_consulta_anidada(nested: ConsultaAnidada) -> ConsultaAnidada:
    return ConsultaAnidada(
        path=nested.path,
        where=_normalizar_lista_condiciones(nested.where),
        select=nested.select,
    )


def _normalizar_paso(paso: PasoConsulta) -> PasoConsulta:
    return PasoConsulta.model_validate({
        "as":     paso.as_,
        "op":     paso.op,
        "from":   paso.from_.value if paso.from_ else None,
        "where":  [c.model_dump() for c in _normalizar_lista_condiciones(paso.where)],
        "select": paso.select,
        "nested": _normalizar_consulta_anidada(paso.nested).model_dump() if paso.nested else None,
        "limit":  paso.limit,
    })


def normalizar_plan(plan: Plan) -> Plan:
    """
    Recibe el Plan validado por Pydantic (salida del Intérprete)
    y devuelve un nuevo Plan con todas las condiciones normalizadas.

    Qué hace:
      - Resuelve todos los 'concept' a path + op + value reales del JSON
      - Normaliza valores directos (tildes, mayúsculas, género, plural)
      - Para PIPE: normaliza cada paso individualmente

    Args:
        plan: Plan validado por el Intérprete.

    Returns:
        Plan con condiciones normalizadas, listo para el Searcher.
    """
    print(f"\n[NORMALIZER] Normalizando plan op={plan.op}")

    # PIPE: normalizar cada paso
    if plan.steps is not None:
        pasos_normalizados = [_normalizar_paso(p) for p in plan.steps]
        return Plan.model_validate({
            "op":    plan.op,
            "steps": [p.model_dump(by_alias=True) for p in pasos_normalizados],
        })

    # GET, FIND, FIND_NESTED, COUNT: normalizar where + nested
    where_normalizado  = _normalizar_lista_condiciones(plan.where)
    nested_normalizado = _normalizar_consulta_anidada(plan.nested) if plan.nested else None

    plan_dict = {
        "op":     plan.op,
        "from":   plan.from_.value if plan.from_ else None,
        "path":   plan.path,
        "where":  [c.model_dump() for c in where_normalizado],
        "select": plan.select,
        "nested": nested_normalizado.model_dump() if nested_normalizado else None,
        "limit":  plan.limit,
    }

    normalizado = Plan.model_validate(plan_dict)

    print(f"[NORMALIZER] Plan normalizado correctamente")
    return normalizado
