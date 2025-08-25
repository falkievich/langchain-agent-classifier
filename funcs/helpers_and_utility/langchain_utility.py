import unicodedata
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence, Union, Tuple

# —————————— Helpers de Normalización ——————————

#-------------------------------- Normaliza texto eliminando tildes y pasando a minúsculas
def normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    clean = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    return clean.strip().lower()

#-------------------------------- Mezcla la utilidad de normalize y clean
def normalize_and_clean(text: str) -> str:
    """
    Normaliza un texto eliminando tildes y diacríticos,
    luego quita todo lo que no sea letra o número,
    y pasa el resultado a minúsculas.
    """
    # 1) Eliminar tildes y diacríticos
    nfkd = unicodedata.normalize("NFD", text or "")
    no_diac = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    # 2) Quitar todo menos letras, números y espacios
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", "", no_diac)
    # 3) Minúsculas y strip
    return cleaned.lower().strip()

# -------------------------------- Helper para parsear booleanos desde string/num
def _to_bool_flag(v: Any) -> bool:
    """
    Convierte entradas tipo 'true/false', 'si/no', '1/0' a booleano.
    Lanza ValueError si no se reconoce.
    """
    s = str(v).strip().lower()
    truthy = {"true", "1", "si", "sí", "verdadero", "yes"}
    falsy  = {"false", "0", "no", "falso", "not", "none"}
    if s in truthy:
        return True
    if s in falsy:
        return False
    raise ValueError(f"Valor booleano no reconocido: {v!r}")

#--------------------------------
DEFAULT_SIM_THRESHOLD = 0.87  # 87%

#--------------------------------
def _get_by_path(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split('.'):
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(part, "")
    return cur

#--------------------------------
def _bag_tokens(s: str) -> str:
    # normaliza fuerte y ordena tokens para reducir efecto del orden
    tks = normalize_and_clean(s).split()
    tks.sort()
    return " ".join(tks)

#--------------------------------
def _similarity(a: str, b: str) -> float:
    """
    Similitud en [0,1] tomando el máximo entre:
    - ratio sobre normalize_and_clean
    - ratio sobre bolsa-de-tokens (orden-insensible)
    """
    a_clean = normalize_and_clean(a)
    b_clean = normalize_and_clean(b)
    r1 = SequenceMatcher(None, a_clean, b_clean).ratio()

    a_bag = _bag_tokens(a)
    b_bag = _bag_tokens(b)
    r2 = SequenceMatcher(None, a_bag, b_bag).ratio()

    return max(r1, r2)

#-------------------------------- 
def es_match_aproximado(needle: str, value: str) -> bool:
    """True si la similitud >= 87%, imprime el porcentaje con valores normalizados."""
    score = _similarity(needle, value)
    return score >= DEFAULT_SIM_THRESHOLD





# —————————— Helpers de Búsqueda en el Json ——————————

#--------------------------------  Buscar clave:valor mediante coincidencias aproximadas
def buscar_entradas_aproximadas_en_lista(
    json_data: Dict[str, Any],
    list_key: str,
    fields: List[str],
    needle: str,
    ignore_keys: Optional[Union[str, Sequence[str]]] = None,
) -> List[Dict[str, Any]]:
    lista = json_data.get(list_key, []) or []
    resultados: List[Dict[str, Any]] = []

    _ignore: List[str] = []
    if isinstance(ignore_keys, str):
        _ignore = [ignore_keys]
    elif isinstance(ignore_keys, (list, tuple, set)):
        _ignore = list(ignore_keys)

    for entry in lista:
        for field in fields:
            val = _get_by_path(entry, field)
            if es_match_aproximado(str(needle), normalize_and_clean(str(val))): # Se normaliza el valor proveniente de la clave:valor
                resultados.append(
                    {k: v for k, v in entry.items() if k not in _ignore} if _ignore else dict(entry)
                )
                break
    return resultados

#-------------------------------- Buscar clave:valor mediante coincidencias exactas
def buscar_entradas_en_lista(
    json_data: Dict[str, Any],
    list_key: str,
    fields: List[str],
    needle: str,
    exact: bool = True,
    ignore_keys: Optional[Union[str, Sequence[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    json_data: diccionario completo cargado desde el JSON del legajo.
    list_key: clave en json_data donde está la lista a buscar (p. ej. "personas_legajo").
    fields: lista de nombres de campo o rutas (p. ej. ["rol", "vinculos.descripcion_vinculo"]).
    needle: valor a buscar en esos campos.
    exact: True para coincidencia exacta, False para búsqueda por subcadena.
    ignore_keys: una clave (str) o lista/tupla de claves a excluir de cada resultado.
    """
    lista = json_data.get(list_key, []) or []
    resultados: List[Dict[str, Any]] = []

    # Normalizo ignore_keys a lista
    _ignore = []
    if isinstance(ignore_keys, str):
        _ignore = [ignore_keys]
    elif isinstance(ignore_keys, (list, tuple, set)):
        _ignore = list(ignore_keys)

    # ----- Paso 1: búsqueda normal -----
    needle = normalize_and_clean(str(needle)) # Se normaliza el valor a buscar
    for entry in lista:
        for field in fields:
            # si el campo es anidado, recorremos la ruta
            val = entry
            for part in field.split('.'):
                if not isinstance(val, dict):
                    val = ""
                    break
                val = val.get(part, "")
            v = normalize_and_clean(str(val)) # v son los valores provenientes de las clave:valor encontradas en la lista. Se los normailiza

            if (exact and v == needle) or (not exact and needle in v):
                resultado = {k: e for k, e in entry.items() if k not in _ignore} if _ignore else dict(entry)
                resultados.append(resultado)
                break

    if resultados:
        return resultados

    # ----- Paso 2: fallback aproximado (87%) -----
    return buscar_entradas_aproximadas_en_lista(
        json_data=json_data,
        list_key=list_key,
        fields=fields,
        needle=needle,
        ignore_keys=ignore_keys,
    )

#-------------------------------- Busca en una lista del JSON las entradas cuyos campos coinciden (exacta o parcialmente) con un valor dado
FieldSpec = Union[str, Tuple[str, str]]  # "ruta" | ("ruta", "alias")

def extraer_campos_en_lista(
    json_data: Dict[str, Any],
    list_key: str,
    fields: List[FieldSpec],
) -> List[Dict[str, Any]]:
    """
    Recorre la ruta 'list_key' (p.ej. 'abogados_legajo.representados') y extrae
    los 'fields' de cada elemento final. Soporta alias ("ruta","alias") y
    acceso al padre con '^.' (p.ej. '^.nombre_completo').
    """
    parts = list_key.split(".")
    nodes: List[Tuple[Any, Any]] = [(json_data, None)]  # (item, parent)

    for part in parts:
        next_nodes: List[Tuple[Any, Any]] = []
        for item, parent in nodes:
            cur = item.get(part, []) if isinstance(item, dict) else []
            if isinstance(cur, list):
                for child in cur:
                    next_nodes.append((child, item))
            elif isinstance(cur, dict):
                next_nodes.append((cur, item))
            # si no hay nada válido, no agregamos
        nodes = next_nodes

    if not nodes:
        return []

    out: List[Dict[str, Any]] = []
    for item, parent in nodes:
        row: Dict[str, Any] = {}
        for fs in fields:
            if isinstance(fs, tuple):
                path, alias = fs
            else:
                path, alias = fs, fs
            if path.startswith("^."):
                value = _get_by_path(parent or {}, path[2:])
            else:
                value = _get_by_path(item or {}, path)
            row[alias] = value
        out.append(row)

    return out