from typing import Any, Dict, List
from funcs.langchain.langchain_utility import buscar_entradas_en_lista

# ————— Tools: materia_delitos —————

IGNORE_MD = ["materia_id", "grado_id"]

# -------------------------------- Listar todos los delitos
def listar_todos_los_delitos(json_data: Dict[str, Any]) -> Dict[str, Any]:
    lst = json_data.get("materia_delitos", []) or []
    # Filtrado de claves en una línea, sin helpers extra
    out = [{k: v for k, v in d.items() if k not in IGNORE_MD} for d in lst]
    return {"materia_delitos": out}

# -------------------------------- Buscar delito por codigo
def buscar_delito_por_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "materia_delitos", ["codigo"], codigo, exact=True, ignore_keys=IGNORE_MD)
    return {"delitos_por_codigo": matches}

# -------------------------------- Buscar delito por descripcion
def buscar_delitos_por_descripcion(json_data: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "materia_delitos", ["descripcion"], descripcion, exact=False, ignore_keys=IGNORE_MD)
    return {"delitos_por_descripcion": matches}

# -------------------------------- Buscar delito por orden
def buscar_delito_por_orden(json_data: Dict[str, Any], orden: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "materia_delitos", ["orden"], orden, exact=True, ignore_keys=IGNORE_MD)
    return {"delitos_por_orden": matches}

# ————— Listado agregado de funciones (materia_delitos) —————
ALL_MATERIA_DELITOS_FUNCS = [
    listar_todos_los_delitos,
    buscar_delito_por_codigo,
    buscar_delitos_por_descripcion,
    buscar_delito_por_orden,
]
