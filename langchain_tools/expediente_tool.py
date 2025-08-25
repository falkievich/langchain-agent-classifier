from funcs.helpers_and_utility.langchain_utility import buscar_entradas_en_lista, extraer_campos_en_lista
from typing import Any, Dict

# ————— Herramientas (Tools) para extracción de información de Expedientes —————

def obtener_info_general_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve la información general del expediente (todos los campos de cabecera_legajo)."""
    return {"cabecera_legajo": json_data.get("cabecera_legajo", {})}

def buscar_estado_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Retorna únicamente el campo 'estado_expediente' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["estado_expediente"],
        needle=json_data.get("cabecera_legajo", {}).get("estado_expediente", ""),
        exact=True
    )
    return {"estado_expediente": matches}

def buscar_materias_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae la lista de 'materias' asociadas al expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["materias"],
        needle="",  # needle vacío para traer todas
        exact=False
    )
    return {"materias": matches}

def buscar_tipo_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae el 'tipo_expediente' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["tipo_expediente"],
        needle="",  # vacío → traer siempre
        exact=False
    )
    return {"tipo_expediente": matches}


def buscar_numero_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae el 'numero_expediente' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["numero_expediente"],
        needle="",  # vacío → traer siempre
        exact=False
    )
    return {"numero_expediente": matches}


def buscar_anio_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae el 'anio_expediente' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["anio_expediente"],
        needle="",  # vacío → traer siempre
        exact=False
    )
    return {"anio_expediente": matches}

def buscar_nivel_acceso(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae el 'nivel_acceso' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["nivel_acceso"],
        needle="",
        exact=False
    )
    return {"nivel_acceso": matches}


def buscar_caratula_publica(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae la 'caratula_publica' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["caratula_publica"],
        needle="",
        exact=False
    )
    return {"caratula_publica": matches}


def buscar_caratula_privada(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae la 'caratula_privada' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["caratula_privada"],
        needle="",
        exact=False
    )
    return {"caratula_privada": matches}


def buscar_tipo_proceso(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae el 'tipo_proceso' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["tipo_proceso"],
        needle="",
        exact=False
    )
    return {"tipo_proceso": matches}


def buscar_etapa_procesal(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae la 'etapa_procesal' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["etapa_procesal"],
        needle="",
        exact=False
    )
    return {"etapa_procesal": matches}


def buscar_cuij(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae el 'cuij' del expediente."""
    matches = buscar_entradas_en_lista(
        json_data={"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        list_key="cabecera_legajo",
        fields=["cuij"],
        needle="",
        exact=False
    )
    return {"cuij": matches}

def buscar_fechas_inicio_y_modificacion_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve siempre las fechas clave del expediente:
    - fecha_inicio: Fecha de inicio del proceso judicial.
    - fecha_modificacion: Fecha de la última modificación del expediente.
    """
    filas = extraer_campos_en_lista(
        {"cabecera_legajo": [json_data.get("cabecera_legajo", {})]},
        "cabecera_legajo",
        ["fecha_inicio", "fecha_modificacion", "organismo_descripcion", "tipo_expediente", "numero_expediente"]
    )
    return {"fechas_inicio_y_modificacion": filas}

# ————— Listado Agregado de Funciones —————
ALL_EXPEDIENTES_FUNCS = [
    obtener_info_general_expediente,
    buscar_estado_expediente,
    buscar_materias_expediente,
    buscar_tipo_expediente,
    buscar_numero_expediente,
    buscar_anio_expediente,
    buscar_nivel_acceso,
    buscar_caratula_publica,
    buscar_caratula_privada,
    buscar_tipo_proceso,
    buscar_etapa_procesal,
    buscar_cuij,
    buscar_fechas_inicio_y_modificacion_expediente,
]
