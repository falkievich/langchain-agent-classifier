import unicodedata
from typing import Any, Dict, List, Optional

from schema.plan_schema import (
    Condicion,
    ConsultaAnidada,
    NodoPrincipal,
    Operacion,
    OperadorCondicion,
    PasoConsulta,
    Plan,
)

# -------- Searcher --------
# Ejecuta el Plan normalizado sobre el JSON del expediente.
# 100% código. Sin LLM.
#
# Recibe: Plan ya normalizado por el Normalizer
#         (todos los conceptos resueltos, todos los valores en formato real del JSON)
# Devuelve: dict con el resultado de la búsqueda
#
# Operaciones soportadas:
#   GET         → lee un campo de un nodo simple (cabecera_legajo, causa)
#   FIND        → filtra items de un nodo lista
#   FIND_NESTED → filtra items + baja a sub-lista dentro de cada resultado
#   COUNT       → cuenta items que cumplen condiciones
#   PIPE        → encadena pasos: el resultado del paso N alimenta el paso N+1


# ────────────────────────────────────────────────────────────────────────────
# 1. Utilidad: normalización de valores para comparación
# ────────────────────────────────────────────────────────────────────────────

def _norm(valor: Any) -> str:
    """
    Normaliza un valor a string minúscula sin tildes para comparación.
    Si el valor es lista, normaliza cada elemento.
    """
    if valor is None:
        return ""
    if isinstance(valor, list):
        return [_norm(v) for v in valor]
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


# ────────────────────────────────────────────────────────────────────────────
# 2. Utilidad: acceso a paths anidados
# ────────────────────────────────────────────────────────────────────────────

def _get_path(item: dict, path: str) -> Any:
    """
    Accede a un campo del item por path con soporte de un nivel de anidamiento.
    Ejemplos:
        "rol"                      → item["rol"]
        "representados.persona_id" → item["representados"]["persona_id"]
        "representados.rol"        → item["representados"]["rol"]
    """
    if "." not in path:
        return item.get(path)

    partes = path.split(".", 1)
    sub = item.get(partes[0])

    if sub is None:
        return None

    # Si el sub-valor es una lista de objetos, extraer el campo de cada uno
    if isinstance(sub, list):
        return [elem.get(partes[1]) for elem in sub if isinstance(elem, dict)]

    if isinstance(sub, dict):
        return sub.get(partes[1])

    return None


# ────────────────────────────────────────────────────────────────────────────
# 3. Evaluador de condiciones
# ────────────────────────────────────────────────────────────────────────────

def _evaluar_condicion(item: dict, condicion: Condicion) -> bool:
    """
    Evalúa si un item cumple una condición.
    Soporta: EQ, CONTAINS, IN, GT, LT.
    Aplica normalización en la comparación para robustez.
    """
    if condicion.path is None:
        # Condición sin path (no debería llegar aquí si el Normalizer hizo su trabajo)
        return True

    valor_item = _get_path(item, condicion.path)
    valor_cond = condicion.value
    op          = condicion.op

    # ── EQ ──────────────────────────────────────────────────────────────────
    if op == OperadorCondicion.EQ:
        if isinstance(valor_item, list):
            return _norm(valor_cond) in _norm(valor_item)
        return _norm(valor_item) == _norm(valor_cond)

    # ── CONTAINS ────────────────────────────────────────────────────────────
    # Para arrays: el valor_cond está en la lista del item
    # Para strings: el valor_cond está contenido en el string del item
    if op == OperadorCondicion.CONTAINS:
        if isinstance(valor_item, list):
            return _norm(valor_cond) in _norm(valor_item)
        if isinstance(valor_item, str):
            return _norm(valor_cond) in _norm(valor_item)
        return False

    # ── IN ──────────────────────────────────────────────────────────────────
    # valor_cond es una lista; el valor del item debe estar en esa lista
    if op == OperadorCondicion.IN:
        if not isinstance(valor_cond, list):
            valor_cond = [valor_cond]
        valores_cond_norm = [_norm(v) for v in valor_cond]
        if isinstance(valor_item, list):
            # Algún elemento del item está en la lista de condición
            return any(v in valores_cond_norm for v in _norm(valor_item))
        return _norm(valor_item) in valores_cond_norm

    # ── GT / LT ─────────────────────────────────────────────────────────────
    if op in (OperadorCondicion.GT, OperadorCondicion.LT):
        try:
            v_item = str(valor_item) if valor_item is not None else ""
            v_cond = str(valor_cond)
            if op == OperadorCondicion.GT:
                return v_item > v_cond
            return v_item < v_cond
        except TypeError:
            return False

    return False


def _cumple_todas(item: dict, condiciones: List[Condicion]) -> bool:
    """Devuelve True si el item cumple TODAS las condiciones (AND lógico)."""
    return all(_evaluar_condicion(item, c) for c in condiciones)


# ────────────────────────────────────────────────────────────────────────────
# 4. Selección de campos
# ────────────────────────────────────────────────────────────────────────────

def _seleccionar(item: dict, select: List[str]) -> dict:
    """
    Devuelve solo los campos indicados en select.
    Si select está vacío, devuelve el item completo.

    Fallback especial: si se pide 'nombre_completo' y el campo no existe
    (o es null) pero el item tiene 'apellido' y 'nombre', los concatena
    automáticamente con el formato "APELLIDO, NOMBRE".
    """
    if not select:
        return item

    resultado = {}
    for campo in select:
        valor = item.get(campo)

        # Fallback: construir nombre_completo desde apellido + nombre
        if campo == "nombre_completo" and not valor:
            apellido = item.get("apellido", "")
            nombre   = item.get("nombre", "")
            if apellido and nombre:
                valor = f"{apellido.upper()}, {nombre.upper()}"

        resultado[campo] = valor

    return resultado


# ────────────────────────────────────────────────────────────────────────────
# 5. Operaciones individuales
# ────────────────────────────────────────────────────────────────────────────

def _ejecutar_get(json_data: dict, plan: Plan) -> dict:
    """
    GET: lee un campo directo de un nodo simple (cabecera_legajo, causa).
    Si path es None devuelve el nodo completo.
    """
    nodo = json_data.get(plan.from_.value, {})

    if not isinstance(nodo, dict):
        return {"error": f"El nodo '{plan.from_.value}' no es un objeto simple."}

    if plan.path:
        valor = nodo.get(plan.path)
        if valor is None:
            return {
                "resultado": None,
                "mensaje": f"El campo '{plan.path}' no existe en '{plan.from_.value}'."
            }
        return {plan.path: valor}

    # Sin path → devuelve el nodo completo filtrado por select
    return _seleccionar(nodo, plan.select)


def _ejecutar_find(json_data: dict, nodo: str, where: List[Condicion], select: List[str], limit: Optional[int]) -> List[dict]:
    """
    FIND: filtra items de un nodo lista y devuelve los campos seleccionados.
    """
    items = json_data.get(nodo, [])

    if not isinstance(items, list):
        return []

    resultados = [
        _seleccionar(item, select)
        for item in items
        if isinstance(item, dict) and _cumple_todas(item, where)
    ]

    if limit is not None:
        resultados = resultados[:limit]

    return resultados


def _ejecutar_find_nested(json_data: dict, plan: Plan) -> List[dict]:
    """
    FIND_NESTED: filtra items del nodo principal y dentro de cada resultado
    baja a una sub-lista, aplica condiciones sobre ella y selecciona campos.

    Soporta dos niveles de anidamiento (nested.nested) para estructuras como:
        abogados_legajo → representados → domicilios
    """
    nested: ConsultaAnidada = plan.nested
    items   = json_data.get(plan.from_.value, [])
    resultado = []

    for item in items:
        if not isinstance(item, dict):
            continue
        if not _cumple_todas(item, plan.where):
            continue

        # Datos del item padre (campos seleccionados del nivel superior)
        datos_padre = _seleccionar(item, plan.select)

        # Sub-lista dentro del item.
        # Puede ser una lista de objetos (domicilios, relacionados, vinculos)
        # o un objeto directo (representados en abogados_legajo).
        # En ambos casos normalizamos a lista para poder iterar.
        sub_items = item.get(nested.path, [])
        if isinstance(sub_items, dict):
            sub_items = [sub_items]  # objeto único → envolver en lista
        elif not isinstance(sub_items, list):
            sub_items = []

        # ── Sin tercer nivel: comportamiento estándar ────────────────────────
        if nested.nested is None:
            sub_resultados = [
                _seleccionar(sub, nested.select)
                for sub in sub_items
                if isinstance(sub, dict) and _cumple_todas(sub, nested.where)
            ]
            resultado.append({
                **datos_padre,
                nested.path: sub_resultados,
            })

        # ── Con tercer nivel: bajar un nivel más dentro de cada sub_item ─────
        else:
            nested2 = nested.nested
            sub_resultados = []
            for sub in sub_items:
                if not isinstance(sub, dict):
                    continue
                if not _cumple_todas(sub, nested.where):
                    continue

                datos_sub = _seleccionar(sub, nested.select)

                # Tercer nivel (ej: representados → domicilios)
                sub_sub_items = sub.get(nested2.path, [])
                if isinstance(sub_sub_items, dict):
                    sub_sub_items = [sub_sub_items]
                elif not isinstance(sub_sub_items, list):
                    sub_sub_items = []

                sub_sub_resultados = [
                    _seleccionar(ss, nested2.select)
                    for ss in sub_sub_items
                    if isinstance(ss, dict) and _cumple_todas(ss, nested2.where)
                ]

                sub_resultados.append({
                    **datos_sub,
                    nested2.path: sub_sub_resultados,
                })

            resultado.append({
                **datos_padre,
                nested.path: sub_resultados,
            })

    return resultado


def _ejecutar_count(json_data: dict, plan: Plan) -> dict:
    """
    COUNT: cuenta items del nodo lista que cumplen las condiciones.
    """
    items = json_data.get(plan.from_.value, [])

    if not isinstance(items, list):
        return {"count": 0}

    total = sum(
        1 for item in items
        if isinstance(item, dict) and _cumple_todas(item, plan.where)
    )

    return {"count": total, "nodo": plan.from_.value}


# ────────────────────────────────────────────────────────────────────────────
# 6. Operación PIPE
# ────────────────────────────────────────────────────────────────────────────

def _resolver_value_from(value_from: str, contexto: dict) -> Optional[List[Any]]:
    """
    Resuelve una referencia value_from="alias.campo" usando el contexto de pasos anteriores.
    Ejemplo: "imputados.persona_id" → lista de persona_ids del paso "imputados"
    """
    if "." not in value_from:
        return None

    alias, campo = value_from.split(".", 1)
    resultados_paso = contexto.get(alias, [])

    if not isinstance(resultados_paso, list):
        return None

    valores = []
    for item in resultados_paso:
        if isinstance(item, dict):
            v = item.get(campo)
            if v is not None:
                if isinstance(v, list):
                    valores.extend(v)
                else:
                    valores.append(v)

    return valores if valores else None


def _inyectar_value_from(condiciones: List[Condicion], contexto: dict) -> List[Condicion]:
    """
    Reemplaza las condiciones con value_from por condiciones IN con los valores reales
    extraídos del contexto del paso anterior.
    """
    resultado = []
    for c in condiciones:
        if c.value_from is not None:
            valores = _resolver_value_from(c.value_from, contexto)
            if valores:
                resultado.append(Condicion(
                    path=c.path,
                    op=OperadorCondicion.IN,
                    value=valores,
                ))
            # Si no hay valores, se omite la condición (no filtrar por vacío)
        else:
            resultado.append(c)
    return resultado


def _ejecutar_paso(json_data: dict, paso: PasoConsulta, contexto: dict) -> Any:
    """Ejecuta un paso individual dentro de un PIPE."""

    # Inyectar referencias cruzadas (value_from) desde el contexto
    where_resuelto = _inyectar_value_from(paso.where, contexto)

    if paso.op == Operacion.FIND:
        return _ejecutar_find(
            json_data,
            nodo=paso.from_.value,
            where=where_resuelto,
            select=paso.select,
            limit=paso.limit,
        )

    if paso.op == Operacion.FIND_NESTED:
        if paso.nested is None:
            return {"error": "FIND_NESTED requiere 'nested' pero no fue provisto en el paso."}
        # Construir un Plan temporal para reutilizar _ejecutar_find_nested
        plan_temp = Plan.model_validate({
            "op":     Operacion.FIND_NESTED,
            "from":   paso.from_.value,
            "where":  [c.model_dump() for c in where_resuelto],
            "select": paso.select,
            "nested": paso.nested.model_dump(),
            "limit":  paso.limit,
        })
        return _ejecutar_find_nested(json_data, plan_temp)

    if paso.op == Operacion.COUNT:
        plan_temp = Plan.model_validate({
            "op":    Operacion.COUNT,
            "from":  paso.from_.value,
            "where": [c.model_dump() for c in where_resuelto],
        })
        return _ejecutar_count(json_data, plan_temp)

    if paso.op == Operacion.GET:
        plan_temp = Plan.model_validate({
            "op":   Operacion.GET,
            "from": paso.from_.value,
            "path": paso.path,
            "select": paso.select,
        })
        return _ejecutar_get(json_data, plan_temp)

    return {"error": f"Operación '{paso.op}' no soportada dentro de PIPE."}


def _ejecutar_pipe(json_data: dict, plan: Plan) -> dict:
    """
    PIPE: ejecuta pasos en secuencia.
    El resultado de cada paso se almacena en el contexto con su alias (as_).
    Las condiciones con value_from se resuelven contra ese contexto.
    """
    contexto: dict = {}
    resultados: dict = {}

    for i, paso in enumerate(plan.steps):
        print(f"[SEARCHER] PIPE paso {i + 1}/{len(plan.steps)}: op={paso.op}, from={paso.from_}")

        resultado_paso = _ejecutar_paso(json_data, paso, contexto)

        # Guardar en contexto con alias si tiene
        if paso.as_:
            contexto[paso.as_] = resultado_paso

        # Guardar en resultados finales
        clave = paso.as_ or f"paso_{i + 1}"
        resultados[clave] = resultado_paso

    return resultados


# ────────────────────────────────────────────────────────────────────────────
# 7. Punto de entrada principal
# ────────────────────────────────────────────────────────────────────────────

def ejecutar_plan(json_data: dict, plan: Plan) -> dict:
    """
    Ejecuta el Plan normalizado sobre el JSON del expediente.

    Args:
        json_data:  JSON completo del expediente.
        plan:       Plan ya normalizado por el Normalizer.

    Returns:
        dict con el resultado de la búsqueda.
        Estructura:
          {
            "op":        "FIND",
            "resultado": [...],   # lista para FIND/FIND_NESTED, dict para GET/COUNT, dict para PIPE
          }
    """
    print(f"\n[SEARCHER] Ejecutando plan op={plan.op}")

    try:
        if plan.op == Operacion.GET:
            resultado = _ejecutar_get(json_data, plan)

        elif plan.op == Operacion.FIND:
            resultado = _ejecutar_find(
                json_data,
                nodo=plan.from_.value,
                where=plan.where,
                select=plan.select,
                limit=plan.limit,
            )

        elif plan.op == Operacion.FIND_NESTED:
            resultado = _ejecutar_find_nested(json_data, plan)

        elif plan.op == Operacion.COUNT:
            resultado = _ejecutar_count(json_data, plan)

        elif plan.op == Operacion.PIPE:
            resultado = _ejecutar_pipe(json_data, plan)

        else:
            return {
                "op":    plan.op,
                "error": f"Operación '{plan.op}' no implementada en el Searcher."
            }

        print(f"[SEARCHER] Búsqueda completada.")
        return {
            "op":        plan.op,
            "resultado": resultado,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "op":    plan.op,
            "error": str(e),
        }
