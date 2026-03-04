from typing import Any, Dict, List, Optional

# -------- Catálogo de campos --------
# Construye dinámicamente el catálogo de campos disponibles por nodo
# a partir del JSON real del expediente.
#
# Propósito:
#   Darle al LLM (Intérprete) información exacta de qué campos existen
#   en cada nodo, para que no invente nombres de campos.
#
# Reglas de construcción:
#   - Solo primer y segundo nivel (campos + sub-listas directas)
#   - Sin duplicados dentro de cada nodo
#   - Sin campos null ni listas vacías (no aportan información)
#   - Sin campos del root (no son consultables por el usuario)
#   - Se construye en cada request (el JSON puede variar entre expedientes)


# Nodos principales consultables (en orden de aparición en el prompt)
NODOS_PRINCIPALES = [
    "cabecera_legajo",
    "causa",
    "personas_legajo",
    "abogados_legajo",
    "funcionarios",
    "dependencias_vistas",
    "radicaciones",
    "materia_delitos",
]

# Sub-listas conocidas por nodo (segundo nivel)
# Solo las que tienen sentido consultar desde el DSL
SUB_LISTAS_POR_NODO: Dict[str, List[str]] = {
    "personas_legajo":    ["domicilios", "relacionados", "caracteristicas", "vinculos"],
    "abogados_legajo":    ["domicilios", "representados"],
    "funcionarios":       ["domicilios"],
    "dependencias_vistas": ["tipos"],
    "cabecera_legajo":    ["materias"],
}


def _campos_de_objeto(obj: dict, excluir_nulos: bool = True) -> List[str]:
    """
    Devuelve los campos de primer nivel de un objeto dict.
    Excluye campos cuyo valor es None o lista vacía si excluir_nulos=True.
    Sin duplicados (garantizado por orden de aparición).
    """
    vistos = set()
    campos = []
    for k, v in obj.items():
        if k in vistos:
            continue
        vistos.add(k)
        if excluir_nulos:
            if v is None:
                continue
            if isinstance(v, list) and len(v) == 0:
                continue
        campos.append(k)
    return campos


def _primer_item(datos: Any) -> Optional[dict]:
    """
    Devuelve el primer item de una lista, o el objeto si es dict.
    Devuelve None si está vacío o no es iterable.
    """
    if isinstance(datos, dict):
        return datos
    if isinstance(datos, list):
        for item in datos:
            if isinstance(item, dict):
                return item
    return None


def _campos_sub_lista(item: dict, nombre_sub: str) -> List[str]:
    """
    Devuelve los campos del primer elemento de una sub-lista dentro de un item.
    Si la sub-lista es un objeto (no lista), devuelve sus campos directamente.
    """
    sub = item.get(nombre_sub)
    if sub is None:
        return []

    primer = _primer_item(sub)
    if primer is None:
        return []

    return _campos_de_objeto(primer, excluir_nulos=False)


def construir_catalogo(json_data: dict) -> Dict[str, Any]:
    """
    Construye el catálogo de campos por nodo a partir del JSON del expediente.

    Estructura devuelta:
    {
        "cabecera_legajo": {
            "tipo": "objeto",
            "campos": ["tipo_expediente", "cuij", ...]
        },
        "personas_legajo": {
            "tipo": "lista",
            "campos": ["persona_id", "nombre_completo", "rol", ...],
            "sub_listas": {
                "domicilios":   ["digital_clase_codigo", "descripcion", ...],
                "relacionados": ["nombre_completo", "tipo", "rol", ...]
            }
        },
        ...
    }
    """
    catalogo: Dict[str, Any] = {}

    for nodo in NODOS_PRINCIPALES:
        datos = json_data.get(nodo)

        if datos is None:
            continue

        # ── Nodo simple (objeto) ─────────────────────────────────────────────
        if isinstance(datos, dict):
            campos = _campos_de_objeto(datos)
            entrada: Dict[str, Any] = {
                "tipo":   "objeto",
                "campos": campos,
            }
            # Sub-listas del nodo simple (ej: cabecera_legajo.materias)
            sub_listas_nodo = SUB_LISTAS_POR_NODO.get(nodo, [])
            sub_listas: Dict[str, List[str]] = {}
            for nombre_sub in sub_listas_nodo:
                campos_sub = _campos_sub_lista(datos, nombre_sub)
                if campos_sub:
                    sub_listas[nombre_sub] = campos_sub
            if sub_listas:
                entrada["sub_listas"] = sub_listas
            catalogo[nodo] = entrada

        # ── Nodo lista ───────────────────────────────────────────────────────
        elif isinstance(datos, list):
            primer = _primer_item(datos)
            if primer is None:
                # Lista vacía → registrar con campos vacíos
                catalogo[nodo] = {"tipo": "lista", "campos": [], "vacio": True}
                continue

            campos = _campos_de_objeto(primer)
            entrada = {
                "tipo":   "lista",
                "campos": campos,
            }

            # Sub-listas del nodo lista
            sub_listas_nodo = SUB_LISTAS_POR_NODO.get(nodo, [])
            sub_listas = {}
            for nombre_sub in sub_listas_nodo:
                campos_sub = _campos_sub_lista(primer, nombre_sub)
                if campos_sub:
                    sub_listas[nombre_sub] = campos_sub
            if sub_listas:
                entrada["sub_listas"] = sub_listas

            catalogo[nodo] = entrada

    return catalogo


def catalogo_a_texto(catalogo: Dict[str, Any]) -> str:
    """
    Convierte el catálogo a texto legible para inyectar en el prompt del Intérprete.

    Formato de salida:
        cabecera_legajo (objeto):
          campos: tipo_expediente, cuij, etapa_procesal_descripcion, ...

        personas_legajo (lista):
          campos: persona_id, nombre_completo, rol, numero_documento, ...
          sub_listas:
            domicilios:   digital_clase_codigo, descripcion
            relacionados: nombre_completo, tipo, rol, persona_id
    """
    lineas = []

    for nodo, info in catalogo.items():
        tipo   = info.get("tipo", "?")
        campos = info.get("campos", [])
        vacio  = info.get("vacio", False)

        if vacio:
            lineas.append(f"  {nodo} ({tipo}): [sin datos en este expediente]")
            continue

        lineas.append(f"  {nodo} ({tipo}):")
        if campos:
            lineas.append(f"    campos: {', '.join(campos)}")

        sub_listas = info.get("sub_listas", {})
        if sub_listas:
            lineas.append(f"    sub_listas:")
            for nombre_sub, campos_sub in sub_listas.items():
                lineas.append(f"      {nombre_sub}: {', '.join(campos_sub)}")

        lineas.append("")  # línea en blanco entre nodos

    return "\n".join(lineas).strip()
