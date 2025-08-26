from funcs.helpers_and_utility.langchain_utility import buscar_entradas_en_lista, _to_bool_flag, extraer_campos_en_lista # Importamos las utilidades
from typing import Any, Dict

# ---------- Tools públicas (todas usan el wrapper, sin repetir código) ----------
def listar_todas_las_dependencias(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve todas las dependencias en 'dependencias_vistas'."""
    deps = json_data.get("dependencias_vistas", []) or []
    return {"dependencias_vistas": deps}

#-------------------------------------------------------------------------
def buscar_dependencias_por_organismo_codigo(json_data: Dict[str, Any], organismo_codigo: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'organismo_codigo'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["organismo_codigo"], list_key="dependencias_vistas", needle=organismo_codigo, exact=True
    )
    return {"dependencias_por_organismo_codigo": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_organismo_descripcion(json_data: Dict[str, Any], organismo_descripcion: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'organismo_descripcion'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["organismo_descripcion"], list_key="dependencias_vistas", needle=organismo_descripcion, exact=True
    )
    return {"dependencias_por_organismo_descripcion": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_codigo(json_data: Dict[str, Any], dependencia_codigo: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'dependencia_codigo'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["dependencia_codigo"], list_key="dependencias_vistas", needle=dependencia_codigo, exact=True
    )
    return {"dependencias_por_codigo": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_dependencia_descripcion(json_data: Dict[str, Any], dependencia_descripcion: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'dependencia_descripcion'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["dependencia_descripcion"], list_key="dependencias_vistas", needle=dependencia_descripcion, exact=True
    )
    return {"dependencias_por_dependencia_descripcion": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_jerarquia(json_data: Dict[str, Any], dependencia_jerarquia: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'dependencia_jerarquia'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["dependencia_jerarquia"], list_key="dependencias_vistas", needle=dependencia_jerarquia, exact=True
    )
    return {"dependencias_por_jerarquia": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_rol(json_data: Dict[str, Any], rol: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'rol'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["rol"], list_key="dependencias_vistas", needle=rol, exact=True
    )
    return {"dependencias_por_rol": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_tipos(json_data: Dict[str, Any], tipos: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'tipos'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["tipos"], list_key="dependencias_vistas", needle=tipos, exact=True
    )
    return {"dependencias_por_tipos": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_clase_descripcion(json_data: Dict[str, Any], clase_descripcion: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'clase_descripcion'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["clase_descripcion"], list_key="dependencias_vistas", needle=clase_descripcion, exact=True
    )
    return {"dependencias_por_clase_descripcion": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_clase_codigo(json_data: Dict[str, Any], clase_codigo: str) -> Dict[str, Any]:
    """Filtra por coincidencia EXACTA en 'clase_codigo'."""
    matches = buscar_entradas_en_lista(
        json_data, fields=["clase_codigo"], list_key="dependencias_vistas", needle=clase_codigo, exact=True
    )
    return {"dependencias_por_clase_codigo": matches}

#-------------------------------------------------------------------------
def buscar_dependencias_por_activo(json_data: Dict[str, Any], activo_flag: Any) -> Dict[str, Any]:
    """
    Filtra por el booleano 'activo'. Aquí no usamos el wrapper porque comparamos booleanos
    (no strings normalizados).
    """
    deps = json_data.get("dependencias_vistas", []) or []
    try:
        flag = activo_flag if isinstance(activo_flag, bool) else _to_bool_flag(activo_flag)
    except ValueError as e:
        return {"error": str(e)}
    matches = [d for d in deps if bool(d.get("activo", False)) == flag]
    return {"dependencias_por_activo": matches}

#-------------------------------------------------------------------------  .
def listar_fechas_depedencias(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve (solo) fecha_desde, fecha_hasta, organismo_descripcion y dependencia_descripcion
    para cada item de dependencias_vistas.
    """
    filas = extraer_campos_en_lista(
        json_data,
        "dependencias_vistas",
        ["fecha_desde", "fecha_hasta", "organismo_descripcion", "dependencia_descripcion", "clase_descripcion"]
    )
    return {"fechas_y_descripciones_dependencias": filas}

#-------------------------------------------------------------------------  Devuelve dependencias por fecha de inicio o fin
def buscar_dependencias_por_fecha(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    """
    Busca dependencias en función de la fecha indicada:
    - fecha_desde: Fecha desde la cual el expediente estuvo en la dependencia.
    - fecha_hasta: Fecha hasta la cual el expediente estuvo en la dependencia.
    """
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="dependencias_vistas",
        fields=["fecha_desde", "fecha_hasta"],
        needle=fecha,
        exact=False
    )
    return {"dependencias_por_fecha": matches}

# ---------- Registro para el agente ----------
ALL_DEPENDENCIAS_FUNCS = [
    listar_todas_las_dependencias,
    buscar_dependencias_por_organismo_codigo,
    buscar_dependencias_por_organismo_descripcion,
    buscar_dependencias_por_codigo,
    buscar_dependencias_por_dependencia_descripcion,
    buscar_dependencias_por_clase_codigo,
    buscar_dependencias_por_clase_descripcion,
    buscar_dependencias_por_activo,
    buscar_dependencias_por_jerarquia,
    buscar_dependencias_por_rol,
    buscar_dependencias_por_tipos,
    listar_fechas_depedencias,
    buscar_dependencias_por_fecha,
]
