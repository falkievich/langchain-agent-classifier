from typing import Any, Dict
from funcs.helpers_and_utility.langchain_utility import buscar_entradas_en_lista, extraer_campos_en_lista

# ————— Tools: radicaciones —————

IGNORE_RAD = ["radicacion_id", "expediente_id"]

# -------------------------------- Listar todas las radicaciones
def listar_todas_las_radicaciones_y_movimiento_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    lst = json_data.get("radicaciones", []) or []
    out = [{k: v for k, v in d.items() if k not in IGNORE_RAD} for d in lst]
    return {"radicaciones": out}

# -------------------------------- Buscar por organismo_actual_codigo (exacto)
def buscar_radicacion_por_organismo_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones", ["organismo_actual_codigo"], codigo, exact=True, ignore_keys=IGNORE_RAD)
    return {"radicaciones_por_organismo_codigo": matches}

# -------------------------------- Buscar por organismo_actual_descripcion (parcial)
def buscar_radicacion_por_organismo_descripcion(json_data: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones", ["organismo_actual_descripcion"], descripcion, exact=False, ignore_keys=IGNORE_RAD)
    return {"radicaciones_por_organismo_descripcion": matches}

#-------------------------------------------------------------------------  Devuelve todas las radicaciones con sus fechas (fecha_desde y fecha_hasta)
def listar_todas_las_fechas_radicaciones(json_data: Dict[str, Any]) -> Dict[str, Any]:
    filas = extraer_campos_en_lista(
        json_data,
        "radicaciones",
        ["organismo_actual_descripcion", "fecha_desde", "fecha_hasta"]
    )
    return {"fechas_radicaciones": filas}

# -------------------------------- Buscar por fecha_desde o fecha_hasta (parcial)
def buscar_radicacion_por_fecha(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones", ["fecha_desde", "fecha_hasta"], fecha, exact=False, ignore_keys=IGNORE_RAD)
    return {"radicaciones_por_fecha": matches}

# -------------------------------- Buscar por motivo_actual_codigo (exacto)
def buscar_radicacion_por_motivo_codigo(json_data: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones", ["motivo_actual_codigo"], codigo, exact=True, ignore_keys=IGNORE_RAD)
    return {"radicaciones_por_motivo_codigo": matches}

# -------------------------------- Buscar por motivo_actual_descripcion (parcial)
def buscar_radicacion_por_motivo_descripcion(json_data: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(json_data, "radicaciones", ["motivo_actual_descripcion"], descripcion, exact=False, ignore_keys=IGNORE_RAD)
    return {"radicaciones_por_motivo_descripcion": matches}

# ————— Listado agregado de funciones (radicaciones) —————
ALL_RADICACIONES_FUNCS = [
    listar_todas_las_radicaciones_y_movimiento_expediente,
    buscar_radicacion_por_organismo_codigo,
    buscar_radicacion_por_organismo_descripcion,
    listar_todas_las_fechas_radicaciones,
    buscar_radicacion_por_fecha,
    buscar_radicacion_por_motivo_codigo,
    buscar_radicacion_por_motivo_descripcion,
]
