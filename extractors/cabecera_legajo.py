"""
extractors/cabecera_legajo.py
─────────────────────────────
Funciones de extracción para la sección "cabecera_legajo" del JSON.
Cada campo relevante tiene su propia función dedicada.
"""
from typing import Any, Dict

# ═══════════════════════════════════════════════════════════════
#  Extracción completa
# ═══════════════════════════════════════════════════════════════

def obtener_cabecera_legajo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve toda la cabecera del legajo."""
    return {"cabecera_legajo": json_data.get("cabecera_legajo", {})}

# ═══════════════════════════════════════════════════════════════
#  Campos individuales de cabecera_legajo
# ═══════════════════════════════════════════════════════════════

def obtener_clave(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"clave": cab.get("clave")}

def obtener_ide(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"ide": cab.get("ide")}

def obtener_orden_sufijo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"orden_sufijo": cab.get("orden_sufijo")}

def obtener_organismo_codigo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"organismo_codigo": cab.get("organismo_codigo")}

def obtener_organismo_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"organismo_descripcion": cab.get("organismo_descripcion")}

def obtener_tipo_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"tipo_expediente": cab.get("tipo_expediente")}

def obtener_numero_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"numero_expediente": cab.get("numero_expediente")}

def obtener_anio_expediente(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"anio_expediente": cab.get("anio_expediente")}

def obtener_estado_expediente_codigo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"estado_expediente_codigo": cab.get("estado_expediente_codigo")}

def obtener_estado_expediente_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"estado_expediente_descripcion": cab.get("estado_expediente_descripcion")}

def obtener_fecha_registro(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"fecha_registro": cab.get("fecha_registro")}

def obtener_nivel_acceso(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"nivel_acceso": cab.get("nivel_acceso")}

def obtener_caratula_publica(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"caratula_publica": cab.get("caratula_publica")}

def obtener_caratula_privada(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"caratula_privada": cab.get("caratula_privada")}

def obtener_fecha_inicio(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"fecha_inicio": cab.get("fecha_inicio")}

def obtener_fecha_modificacion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"fecha_modificacion": cab.get("fecha_modificacion")}

def obtener_usuario_alta(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"usuario_alta": cab.get("usuario_alta")}

def obtener_usuario_baja(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"usuario_baja": cab.get("usuario_baja")}

def obtener_usuario_modificacion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"usuario_modificacion": cab.get("usuario_modificacion")}

def obtener_dependencia_radicacion_codigo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"dependencia_radicacion_codigo": cab.get("dependencia_radicacion_codigo")}

def obtener_dependencia_radicacion_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"dependencia_radicacion_descripcion": cab.get("dependencia_radicacion_descripcion")}

def obtener_tipo_proceso(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"tipo_proceso": cab.get("tipo_proceso")}

def obtener_etapa_procesal_codigo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"etapa_procesal_codigo": cab.get("etapa_procesal_codigo")}

def obtener_etapa_procesal_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"etapa_procesal_descripcion": cab.get("etapa_procesal_descripcion")}

def obtener_prioridad(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"prioridad": cab.get("prioridad")}

def obtener_cuij(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"cuij": cab.get("cuij")}

def obtener_materias_cabecera(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve la lista de materias dentro de cabecera_legajo."""
    cab = json_data.get("cabecera_legajo", {})
    return {"materias": cab.get("materias", [])}

def obtener_ubicacion_actual_codigo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"ubicacion_actual_codigo": cab.get("ubicacion_actual_codigo")}

def obtener_ubicacion_actual_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"ubicacion_actual_descripcion": cab.get("ubicacion_actual_descripcion")}

def obtener_secretaria_codigo(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"secretaria_codigo": cab.get("secretaria_codigo")}

def obtener_secretaria_descripcion(json_data: Dict[str, Any]) -> Dict[str, Any]:
    cab = json_data.get("cabecera_legajo", {})
    return {"secretaria_descripcion": cab.get("secretaria_descripcion")}
