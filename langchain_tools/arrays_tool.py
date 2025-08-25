from typing import Any, Dict
from funcs.helpers_and_utility.langchain_utility import buscar_entradas_en_lista

IGNORE_FUNCIONARIOS = ["id"]
IGNORE_CAUSA = ["causa_id"]

# -------------------------------- Listar todos los funcionarios
def listar_todos_los_funcionarios(json_data: Dict[str, Any]) -> Dict[str, Any]:
    funcionarios = json_data.get("funcionarios", []) or []
    out = [{k: v for k, v in f.items() if k not in IGNORE_FUNCIONARIOS} for f in funcionarios]
    return {"funcionarios": out}

# -------------------------------- Buscar funcionario por nombre
def buscar_funcionario_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="funcionarios",
        fields=["nombre"],
        needle=nombre,
        exact=False,  # parcial por si el usuario no pone el nombre exacto
        ignore_keys=IGNORE_FUNCIONARIOS
    )
    return {"funcionarios_por_nombre": matches}

# -------------------------------- Listar todas las causas
def listar_todas_las_causas(json_data: Dict[str, Any]) -> Dict[str, Any]:
    causas = json_data.get("causa", []) or []
    out = [{k: v for k, v in c.items() if k not in IGNORE_CAUSA} for c in causas]
    return {"causa": out}

# -------------------------------- Buscar causa por descripcion
def buscar_causa_por_descripcion(json_data: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="causa",
        fields=["descripcion"],
        needle=descripcion,
        exact=False,  # parcial por flexibilidad
        ignore_keys=IGNORE_CAUSA
    )
    return {"causa_por_descripcion": matches}

# -------------------------------- Listar todas las clasificaciones de legajo
def listar_todas_las_clasificaciones_legajo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    clasifs = json_data.get("clasificadores_legajo", []) or []
    return {"clasificadores_legajo": clasifs}

# -------------------------------- Buscar clasificacion de legajo por descripcion
def buscar_clasificacion_legajo_por_descripcion(json_data: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="clasificadores_legajo",
        fields=["clasificador"],
        needle=descripcion,
        exact=False
    )
    return {"clasificador_legajo_por_descripcion": matches}

# ————— Listado agregado de funciones —————
ALL_ARRAYS_FUNCS = [
    listar_todos_los_funcionarios,
    buscar_funcionario_por_nombre,
    listar_todas_las_causas,
    buscar_causa_por_descripcion,
    listar_todas_las_clasificaciones_legajo,
    buscar_clasificacion_legajo_por_descripcion,
]
