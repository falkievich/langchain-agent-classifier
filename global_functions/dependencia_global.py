from typing import Any, Dict
from langchain_tools.dependencias_vistas_tool import (
    buscar_dependencias_por_organismo_codigo,
    buscar_dependencias_por_organismo_descripcion,
    buscar_dependencias_por_codigo,
    buscar_dependencias_por_dependencia_descripcion,
    buscar_dependencias_por_jerarquia,
    buscar_dependencias_por_rol,
    buscar_dependencias_por_tipos,
    buscar_dependencias_por_clase_descripcion,
    buscar_dependencias_por_clase_codigo,
    buscar_dependencias_por_activo,
    buscar_dependencias_por_fecha,
)
from global_functions.json_fallback import buscar_en_json_por_dominio

# Lista de filtros válidos para buscar_dependencia
DEPENDENCIA_FILTROS_DISPONIBLES = [
    "organismo_codigo_dependencia: Filtra dependencias por el código del organismo (ej: 1C01MR).",
    "organismo_descripcion_dependencia: Filtra dependencias por la descripción del organismo (ej: Mesa Receptora Única).",
    "dependencia_codigo: Filtra dependencias por su código específico (ej: MRU01).",
    "dependencia_descripcion: Filtra dependencias por su descripción (ej: Mesa de Entradas Central).",
    "dependencia_jerarquia: Filtra dependencias por nivel de jerarquía numérico (ej: 0, 1, 2...).",
    "dependencia_rol: Filtra dependencias por el rol asignado (ej: INGRESO).",
    "dependencia_tipo: Filtra dependencias por el tipo (ej: Mesa de entradas).",
    "clase_descripcion_dependencia: Filtra dependencias por descripción de clase (ej: Ingreso).",
    "clase_codigo_dependencia: Filtra dependencias por código de clase (ej: CLF0).",
    "activo_dependencia: Filtra dependencias activas o inactivas (true/false).",
    "fecha_dependencia: Filtra dependencias por fechas de inicio o fin (formato AAAA-MM-DD).",
]

def buscar_dependencia(json_data: Dict[str, Any], filtro: str, valor: Any) -> Dict[str, Any]:
    """
    Busca información de dependencias según el filtro especificado.
    Si no se encuentra nada, usa el fallback global.

    Filtros disponibles: DEPENDENCIA_FILTROS_DISPONIBLES
    """
    if filtro == "organismo_codigo_dependencia":
        res = buscar_dependencias_por_organismo_codigo(json_data, valor)
    elif filtro == "organismo_descripcion_dependencia":
        res = buscar_dependencias_por_organismo_descripcion(json_data, valor)
    elif filtro == "dependencia_codigo":
        res = buscar_dependencias_por_codigo(json_data, valor)
    elif filtro == "dependencia_descripcion":
        res = buscar_dependencias_por_dependencia_descripcion(json_data, valor)
    elif filtro == "dependencia_jerarquia":
        res = buscar_dependencias_por_jerarquia(json_data, valor)
    elif filtro == "dependencia_rol":
        res = buscar_dependencias_por_rol(json_data, valor)
    elif filtro == "dependencia_tipo":
        res = buscar_dependencias_por_tipos(json_data, valor)
    elif filtro == "clase_descripcion_dependencia":
        res = buscar_dependencias_por_clase_descripcion(json_data, valor)
    elif filtro == "clase_codigo_dependencia":
        res = buscar_dependencias_por_clase_codigo(json_data, valor)
    elif filtro == "activo_dependencia":
        res = buscar_dependencias_por_activo(json_data, valor)
    elif filtro == "fecha_dependencia":
        res = buscar_dependencias_por_fecha(json_data, valor)
    else:
        return {
            "error": f"Filtro '{filtro}' no reconocido en buscar_dependencia. "
                     f"Opciones válidas: {DEPENDENCIA_FILTROS_DISPONIBLES}"
        }

    if not res or (isinstance(res, dict) and not any(res.values())):
        return {
            "mensaje": "No se encontraron resultados específicos. "
                       "Mostrando coincidencias aproximadas dentro del dominio 'dependencias'.",
            "fallback": buscar_en_json_por_dominio(json_data, "dependencias", valor)
        }

    return res