from typing import Any, Dict, List, Optional, Set

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

# Campos que identifican a una persona (si están en un nodo/sub-lista,
# ese nodo/sub-lista "contiene personas con identidad propia")
CAMPOS_IDENTIDAD: Set[str] = {"numero_documento", "nombre_completo", "cuil"}

# Sub-listas conocidas por nodo (segundo nivel)
# Solo las que tienen sentido consultar desde el DSL
SUB_LISTAS_POR_NODO: Dict[str, List[str]] = {
    "personas_legajo":    ["domicilios", "relacionados", "caracteristicas", "vinculos"],
    "abogados_legajo":    ["domicilios", "representados"],
    "funcionarios":       ["domicilios"],
    "dependencias_vistas": ["tipos"],
    "cabecera_legajo":    ["materias"],
}

# Sub-sub-listas a inspeccionar para detectar fuentes de identidad y contacto
# Clave: (nodo, sub_lista), Valor: nombre de la sub-sub-lista dentro de cada ítem de sub_lista
SUB_SUB_LISTAS_IDENTIDAD: Dict[tuple, str] = {
    ("personas_legajo", "relacionados"): "domicilios",
    ("abogados_legajo", "representados"): "domicilios",
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


def construir_catalogo(json_data: dict, incluir_fuentes_identidad: bool = True) -> Dict[str, Any]:
    """
    Construye el catálogo de campos por nodo a partir del JSON del expediente.
    Si incluir_fuentes_identidad=True, agrega la clave "_fuentes_identidad" con
    todas las ubicaciones donde hay numero_documento / nombre_completo.
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
                catalogo[nodo] = {"tipo": "lista", "campos": [], "vacio": True}
                continue

            campos = _campos_de_objeto(primer)
            entrada = {
                "tipo":   "lista",
                "campos": campos,
            }

            # Sub-listas: usar unión de múltiples ítems para no perder campos
            sub_listas_nodo = SUB_LISTAS_POR_NODO.get(nodo, [])
            sub_listas = {}
            for nombre_sub in sub_listas_nodo:
                campos_sub = _campos_sub_lista_union(datos, nombre_sub)
                if campos_sub:
                    sub_listas[nombre_sub] = campos_sub
            if sub_listas:
                entrada["sub_listas"] = sub_listas

            catalogo[nodo] = entrada

    # Agregar mapa de fuentes de identidad para que el LLM sepa dónde hay DNI/nombres
    if incluir_fuentes_identidad:
        catalogo["_fuentes_identidad"] = _detectar_fuentes_identidad(json_data)

    return catalogo


def catalogo_a_texto(catalogo: Dict[str, Any]) -> str:
    """
    Convierte el catálogo a texto legible para inyectar en el prompt del Intérprete.

    Incluye:
      1. Campos por nodo (estructura del JSON)
      2. Sección "UBICACIONES DE NOMBRE/DNI" que lista TODOS los nodos y
         sub-listas donde existe numero_documento, para que el LLM sepa que
         una pregunta sobre "todos los DNI" requiere buscar en múltiples lugares.
    """
    lineas = []

    # ── Sección 1: estructura de campos por nodo ─────────────────────────────
    lineas.append("### Estructura de campos por nodo:")
    lineas.append("")

    for nodo, info in catalogo.items():
        if nodo.startswith("_"):
            continue  # saltar claves internas

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

        lineas.append("")

    # ── Sección 2: mapa de fuentes de identidad ──────────────────────────────
    fuentes = catalogo.get("_fuentes_identidad", [])
    if fuentes:
        lineas.append("### UBICACIONES DE NOMBRE/DNI/CONTACTO en este expediente:")
        lineas.append("# IMPORTANTE: si la pregunta pide 'todos los DNI', 'todas las personas'")
        lineas.append("# o 'todos los celulares/emails', el plan DEBE cubrir TODAS las fuentes.")
        lineas.append("# Ignorar alguna fuente producirá resultados incompletos.")
        lineas.append("# NOTA: 'X→Y' indica sub-sub-lista: primero FIND_NESTED a X, luego nested a Y.")
        lineas.append("")
        for f in fuentes:
            nodo = f["nodo"]
            sub  = f.get("sub_lista")
            ci   = ", ".join(f["campos_identidad"])
            if sub and "→" in sub:
                lineas.append(f"  - {nodo} → {sub} → campos: {ci}")
            elif sub:
                lineas.append(f"  - {nodo} → sub_lista '{sub}' → campos: {ci}")
            else:
                lineas.append(f"  - {nodo} (nivel principal) → campos: {ci}")
        lineas.append("")

    return "\n".join(lineas).strip()


# ────────────────────────────────────────────────────────────────────────────
# Nuevas utilidades: detección dinámica de identidad
# ────────────────────────────────────────────────────────────────────────────

def _campos_de_lista_union(items: list, max_items: int = 5) -> List[str]:
    """
    Une los campos de los primeros max_items elementos de una lista.
    Garantiza que no se pierdan campos que solo aparecen en algunos ítems.
    """
    vistos: Set[str] = set()
    campos: List[str] = []
    for item in items[:max_items]:
        if not isinstance(item, dict):
            continue
        for k in item:
            if k not in vistos:
                vistos.add(k)
                campos.append(k)
    return campos


def _campos_sub_lista_union(items: list, nombre_sub: str, max_items: int = 5) -> List[str]:
    """
    Une los campos de la sub-lista 'nombre_sub' inspeccionando hasta max_items
    elementos padres (por si no todos los ítems tienen la sub-lista poblada).
    Soporta sub-lista como lista de objetos o como objeto directo.
    """
    vistos: Set[str] = set()
    campos: List[str] = []
    for item in items[:max_items]:
        if not isinstance(item, dict):
            continue
        sub = item.get(nombre_sub)
        if sub is None:
            continue
        primer = _primer_item(sub)
        if primer is None:
            continue
        for k in primer:
            if k not in vistos:
                vistos.add(k)
                campos.append(k)
    return campos


def _detectar_fuentes_identidad(json_data: dict) -> List[Dict[str, Any]]:
    """
    Escanea el JSON completo y devuelve todas las ubicaciones donde existen
    campos de identidad (numero_documento / nombre_completo) o de contacto
    (digital_clase_codigo en domicilios).

    Retorna lista de dicts:
        [
          {"nodo": "personas_legajo",  "sub_lista": None,               "campos_identidad": [...]},
          {"nodo": "personas_legajo",  "sub_lista": "relacionados",      "campos_identidad": [...]},
          {"nodo": "personas_legajo",  "sub_lista": "relacionados→domicilios", "campos_identidad": [...]},
          {"nodo": "abogados_legajo",  "sub_lista": None,               "campos_identidad": [...]},
          {"nodo": "funcionarios",     "sub_lista": None,               "campos_identidad": [...]},
        ]
    """
    # Campos de contacto también relevantes para búsquedas de celulares/emails
    CAMPOS_CONTACTO: Set[str] = {"digital_clase_codigo"}
    CAMPOS_BUSCAR = CAMPOS_IDENTIDAD | CAMPOS_CONTACTO

    fuentes = []

    for nodo in NODOS_PRINCIPALES:
        datos = json_data.get(nodo)
        if datos is None:
            continue

        # ── Nodo simple (dict) ───────────────────────────────────────────────
        if isinstance(datos, dict):
            presentes = [c for c in CAMPOS_IDENTIDAD if datos.get(c) is not None]
            if presentes:
                fuentes.append({"nodo": nodo, "sub_lista": None, "campos_identidad": presentes})
            # Sub-listas del objeto
            for nombre_sub in SUB_LISTAS_POR_NODO.get(nodo, []):
                sub = datos.get(nombre_sub)
                # sub puede ser dict (representados) o lista (domicilios)
                sub_como_lista = [sub] if isinstance(sub, dict) else (sub if isinstance(sub, list) else [])
                campos_sub = _campos_de_lista_union(sub_como_lista) if sub_como_lista else []
                presentes_sub = [c for c in CAMPOS_IDENTIDAD if c in campos_sub]
                if presentes_sub:
                    fuentes.append({"nodo": nodo, "sub_lista": nombre_sub, "campos_identidad": presentes_sub})

        # ── Nodo lista ───────────────────────────────────────────────────────
        elif isinstance(datos, list):
            # Campos del nivel principal (unión de varios ítems)
            campos_union = _campos_de_lista_union(datos)
            presentes = [c for c in CAMPOS_IDENTIDAD if c in campos_union]
            if presentes:
                fuentes.append({"nodo": nodo, "sub_lista": None, "campos_identidad": presentes})

            # Sub-listas de segundo nivel
            for nombre_sub in SUB_LISTAS_POR_NODO.get(nodo, []):
                campos_sub = _campos_sub_lista_union(datos, nombre_sub)
                presentes_sub = [c for c in CAMPOS_IDENTIDAD if c in campos_sub]
                if presentes_sub:
                    fuentes.append({"nodo": nodo, "sub_lista": nombre_sub, "campos_identidad": presentes_sub})

                # Sub-sub-listas de tercer nivel (ej: personas_legajo → relacionados → domicilios)
                sub_sub_key = (nodo, nombre_sub)
                nombre_sub_sub = SUB_SUB_LISTAS_IDENTIDAD.get(sub_sub_key)
                if nombre_sub_sub:
                    campos_sub_sub = _detectar_campos_sub_sub(datos, nombre_sub, nombre_sub_sub)
                    presentes_sub_sub = [c for c in CAMPOS_BUSCAR if c in campos_sub_sub]
                    if presentes_sub_sub:
                        fuentes.append({
                            "nodo": nodo,
                            "sub_lista": f"{nombre_sub}→{nombre_sub_sub}",
                            "campos_identidad": presentes_sub_sub,
                        })

    return fuentes


def _detectar_campos_sub_sub(items: list, nombre_sub: str, nombre_sub_sub: str, max_items: int = 5) -> List[str]:
    """
    Detecta los campos disponibles en el tercer nivel de anidamiento.
    Ejemplo: personas_legajo[*].relacionados[*].domicilios[*]
    """
    vistos: Set[str] = set()
    campos: List[str] = []
    for item in items[:max_items]:
        if not isinstance(item, dict):
            continue
        sub = item.get(nombre_sub)
        if sub is None:
            continue
        # sub puede ser lista o dict
        sub_items = sub if isinstance(sub, list) else [sub]
        for sub_item in sub_items:
            if not isinstance(sub_item, dict):
                continue
            sub_sub = sub_item.get(nombre_sub_sub)
            if not sub_sub:
                continue
            sub_sub_items = sub_sub if isinstance(sub_sub, list) else [sub_sub]
            for ss_item in sub_sub_items:
                if not isinstance(ss_item, dict):
                    continue
                for k in ss_item:
                    if k not in vistos:
                        vistos.add(k)
                        campos.append(k)
    return campos

