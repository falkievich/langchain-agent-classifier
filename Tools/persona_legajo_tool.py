from funcs.langchain.langchain_utility import buscar_entradas_en_lista, _to_bool_flag # Importamos las utilidades
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
]
