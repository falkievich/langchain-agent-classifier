from funcs.helpers_and_utility.langchain_utility import buscar_entradas_en_lista, _to_bool_flag, extraer_campos_en_lista # Importamos las utilidades
from typing import Any, Dict, List

# ————— Herramientas (Tools) para extracción en el JSON —————
#-------------------------------------------------------------------------  # Busca personas por coincidencia EXACTA de 'numero_documento' (DNI).
def buscar_persona_por_numero_documento_dni(json_data: Dict[str, Any], numero_documento: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["numero_documento"],
        needle=numero_documento,
        exact=True
    )
    return {"personas_por_numero_documento": matches}

#-------------------------------------------------------------------------  # Busca personas por coincidencia EXACTA de 'cuil'.
def buscar_persona_por_numero_cuil(json_data: Dict[str, Any], numero_cuil: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["cuil"],
        needle=numero_cuil,
        exact=True
    )
    return {"personas_por_cuil": matches}

#-------------------------------------------------------------------------
def buscar_persona_por_rol(json_data: Dict[str, Any], rol: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["rol"],
        needle=rol,
        exact=False
    )
    return {"personas_por_rol": matches}

#-------------------------------------------------------------------------  # Devuelve personas cuyo 'rol' contenga el valor indicado (búsqueda parcial).
def buscar_persona_por_descripcion_vinculo(json_data: Dict[str, Any], descripcion_vinculo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["vinculos.descripcion_vinculo"],
        needle=descripcion_vinculo,
        exact=False
    )
    return {"personas_por_vinculo": matches}

#-------------------------------------------------------------------------  # Devuelve l
def buscar_persona_por_codigo_vinculo(json_data: Dict[str, Any], codigo_vinculo: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["vinculos.codigo_vinculo"],
        needle=codigo_vinculo,
        exact=True
    )
    return {"personas_por_codigo_vinculo": matches}

# -------------------------------- Buscar por nombre / apellido / nombre_completo
def buscar_persona_por_nombre(json_data: Dict[str, Any], nombre: str) -> Dict[str, Any]:
    """Trae las personas cuyo 'nombre', 'apellido' o 'nombre_completo' coincida exactamente con el valor dado."""
    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="personas_legajo",
        fields=["nombre", "apellido", "nombre_completo"],
        needle=nombre,
        exact=True
    )
    return {"personas_por_nombre": matches}

# -------------------------------- Buscar por tipo_documento
def buscar_persona_por_tipo_documento(json_data: Dict[str, Any], tipo_documento: str) -> Dict[str, Any]:
    """Trae todas las personas con el mismo 'tipo_documento' (coincidencia exacta, case/acentos-insensitive)."""
    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="personas_legajo",
        fields=["tipo_documento"],
        needle=tipo_documento,
        exact=False
    )
    return {"personas_por_tipo_documento": matches}

# -------------------------------- Buscar por estado de detención (True/False)
def buscar_persona_por_estado_detencion(json_data: Dict[str, Any], estado_boleano: Any) -> Dict[str, Any]:
    """Trae todas las personas cuyo 'es_detenido' coincide con el booleano indicado (true/false)."""
    flag = _to_bool_flag(estado_boleano)  # admite 'true/false', 'si/no', '1/0', etc.
    personas = json_data.get("personas_legajo", [])
    matches: List[Dict[str, Any]] = [
        p for p in personas
        if isinstance(p.get("es_detenido"), bool) and p.get("es_detenido") == flag 
    ]
    return {"personas_por_estado_detencion": matches}

#-------------------------------------------------------------------------  # Devuelve la persona o personas que coincidan con la fecha de nacimiento exacta
def buscar_persona_por_fecha_nacimiento(json_data: Dict[str, Any], fecha_nacimiento: str) -> Dict[str, Any]:
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["fecha_nacimiento"],
        needle=fecha_nacimiento,
        exact=False
    )
    return {"personas_por_fecha_nacimiento": matches}

#-------------------------------------------------------------------------  Devuelve todas las personas con sus fechas de participación
def listar_todas_las_fecha_persona_participacion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve todas las personas con sus fechas de participación.
    Retorna: nombre_completo, rol, fecha_desde, fecha_hasta.
    """
    filas = extraer_campos_en_lista(
        json_data,
        "personas_legajo",
        ["nombre_completo","numero_documento" , "rol", "fecha_desde", "fecha_hasta"]
    )
    return {"personas_participacion": filas}

#-------------------------------------------------------------------------  Devuelve todas las personas con sus vínculos
def listar_todas_las_fechas_persona_vinculos(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve todas las personas con sus vínculos.
    Retorna: nombre_completo, rol, vinculos.descripcion_vinculo,
             vinculos.fecha_desde, vinculos.fecha_hasta.
    """
    filas = extraer_campos_en_lista(
        json_data,
        "personas_legajo",
        ["nombre_completo","numero_documento","rol", "vinculos.descripcion_vinculo", "vinculos.fecha_desde", "vinculos.fecha_hasta"]
    )
    return {"personas_vinculos": filas}


#-------------------------------------------------------------------------  Devuelve personas cuya fecha de participación coincida con la fecha indicada
def buscar_persona_por_fecha_participacion(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    """
    Busca personas en el legajo que coincidan con una fecha de participación:
    - fecha_desde: Fecha desde la cual la persona está involucrada en el caso judicial.
    - fecha_hasta: Fecha hasta la cual la persona estuvo involucrada en el caso judicial.
    """
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["fecha_desde", "fecha_hasta"],
        needle=fecha,
        exact=False
    )
    return {"personas_por_fecha_participacion": matches}

#-------------------------------------------------------------------------  Devuelve personas según la fecha de inicio o fin del vínculo
def buscar_persona_por_fecha_vinculo(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    """
    Busca personas en el legajo que tengan vínculos activos o finalizados en la fecha indicada:
    - vinculos.fecha_desde: Fecha desde la cual inició el vínculo con el expediente.
    - vinculos.fecha_hasta: Fecha en la cual finalizó el vínculo con el expediente.
    """
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="personas_legajo",
        fields=["vinculos.fecha_desde", "vinculos.fecha_hasta"],
        needle=fecha,
        exact=False
    )
    return {"personas_por_fecha_vinculo": matches}

# Lista todos los campos de personas_lagajos
FIELDS_PERSONA_LEGAJO = [
    "nombre", "apellido", "nombre_completo",
    "tipo_documento", "numero_documento", "cuil",
    "fecha_nacimiento", "genero", "rol",
    "es_detenido", "fecha_desde", "fecha_hasta",
    "vinculos.codigo_vinculo", "vinculos.descripcion_vinculo",
    "vinculos.fecha_desde", "vinculos.fecha_hasta",
]

def todas_las_personas_en_legajo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    filas = extraer_campos_en_lista(
        json_data=json_data,
        list_key="personas_legajo",
        fields=FIELDS_PERSONA_LEGAJO,
    )
    return {"personas_legajo": filas}

# ————— Listado Agregado de Funciones (personas_legajo) —————
ALL_PERSONAS_FUNCS = [
    buscar_persona_por_numero_documento_dni,
    buscar_persona_por_numero_cuil,
    buscar_persona_por_rol,
    buscar_persona_por_descripcion_vinculo,
    buscar_persona_por_codigo_vinculo,
    buscar_persona_por_nombre,
    buscar_persona_por_tipo_documento,
    buscar_persona_por_estado_detencion,
    buscar_persona_por_fecha_nacimiento,
    listar_todas_las_fecha_persona_participacion,
    listar_todas_las_fechas_persona_vinculos,
    buscar_persona_por_fecha_participacion,
    buscar_persona_por_fecha_vinculo,
    todas_las_personas_en_legajo,
]
