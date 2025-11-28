from typing import Dict, Any
from langchain_core.tools import Tool as LangChainTool

# Importamos la función global y su lista de filtros disponibles
from global_functions.abogado_global import buscar_abogado, ABOGADO_FILTROS_DISPONIBLES
from global_functions.persona_global import buscar_persona, PERSONA_FILTROS_DISPONIBLES
from global_functions.dependencia_global import buscar_dependencia, DEPENDENCIA_FILTROS_DISPONIBLES
from global_functions.radicacion_global import buscar_radicacion, RADICACION_FILTROS_DISPONIBLES
from global_functions.delito_global import buscar_delito, DELITO_FILTROS_DISPONIBLES
from global_functions.expediente_global import obtener_dato_expediente, EXPEDIENTE_CAMPOS_DISPONIBLES
from global_functions.array_global import (
    buscar_funcionario, FUNCIONARIO_FILTROS_DISPONIBLES,
    buscar_causa, CAUSA_FILTROS_DISPONIBLES,
    buscar_clasificacion_legajo, CLASIFICACION_LEGAJO_FILTROS_DISPONIBLES,
)

def make_domain_search_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para búsquedas por dominio.
    """
    tools = []

    # Abogado
    tools.append(
        LangChainTool(
            name="buscar_abogado",
            func=lambda filtro, valor: buscar_abogado(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=f"Busca información de abogados según el filtro especificado. "
                        f"Filtros disponibles: {ABOGADO_FILTROS_DISPONIBLES}"
        )
    )
    # Personas en el Legajo
    tools.append(
        LangChainTool(
            name="buscar_persona",
            func=lambda filtro, valor: buscar_persona(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=(
                "Busca información de personas según el filtro especificado. "
                f"Filtros disponibles: {PERSONA_FILTROS_DISPONIBLES}. "
                "Notas importantes: "
                "- Para 'estado_detencion' el valor debe ser 'true' (detenidos) o 'false' (no detenidos). "
                "- Para 'dni' el valor debe ser un número de 7 u 8 dígitos (con o sin puntos), ej: 45678566 o 45.678.566. "
                "- Para 'cuil' el valor debe ser de 11 dígitos, con o sin guiones/puntos, ej: 20-45678566-1 o 20.456785661. "
                "- Para 'rol' debes usar una descripción como ACTOR, DILIGENCIANTE o DEMANDADO. "
                "- Para 'descripcion_vinculo' usa descripciones como Abogado patrocinante o Demandante. "
                "- Para 'tipo_documento' valores como DNI o Pasaporte."
            )
        )
    )
    # Dependencia
    tools.append(
        LangChainTool(
            name="buscar_dependencia",
            func=lambda filtro, valor: buscar_dependencia(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=f"Busca información de dependencias según el filtro especificado. "
                        f"Filtros disponibles: {DEPENDENCIA_FILTROS_DISPONIBLES}"
                            f"- Para el filtro 'activo' el valor debe ser 'true' (dependencias activas) o 'false' (dependencias no activas)."
        )
    )
    # Radicación
    tools.append(
        LangChainTool(
            name="buscar_radicacion",
            func=lambda filtro, valor: buscar_radicacion(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=f"Busca información de radicaciones según el filtro especificado. "
                        f"Filtros disponibles: {RADICACION_FILTROS_DISPONIBLES}"
        )
    )
    # Delitos
    tools.append(
        LangChainTool(
            name="buscar_delito",
            func=lambda filtro, valor: buscar_delito(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=f"Busca información de delitos según el filtro especificado. "
                        f"Filtros disponibles: {DELITO_FILTROS_DISPONIBLES}"
        )
    )
    # Funcionario
    tools.append(
        LangChainTool(
            name="buscar_funcionario",
            func=lambda filtro, valor: buscar_funcionario(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=f"Busca información de funcionarios según el filtro especificado. "
                        f"Filtros disponibles: {FUNCIONARIO_FILTROS_DISPONIBLES}"
        )
    )
    # Causa
    tools.append(
        LangChainTool(
            name="buscar_causa",
            func=lambda filtro, valor: buscar_causa(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=f"Busca información de causas según el filtro especificado. "
                        f"Filtros disponibles: {CAUSA_FILTROS_DISPONIBLES}"
        )
    )
    # Clasificación de Legajo
    tools.append(
        LangChainTool(
            name="buscar_clasificacion_legajo",
            func=lambda filtro, valor: buscar_clasificacion_legajo(json_data, filtro, valor[0] if isinstance(valor, list) and len(valor) == 1 else valor),
            description=f"Busca información de clasificaciones de legajo según el filtro especificado. "
                        f"Filtros disponibles: {CLASIFICACION_LEGAJO_FILTROS_DISPONIBLES}"
        )
    )
    # Expediente
    tools.append(
        LangChainTool(
            name="obtener_dato_expediente",
            func=lambda campo: obtener_dato_expediente(json_data, campo),
            description=f"Devuelve información del expediente según el campo especificado. "
                        f"Campos disponibles: {EXPEDIENTE_CAMPOS_DISPONIBLES}"
        )
    )
    return tools
