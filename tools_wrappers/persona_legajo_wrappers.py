from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.persona_legajo_tool import (
    buscar_persona_por_numero_documento_dni,
    buscar_persona_por_numero_cuil,
    buscar_persona_por_rol,
    buscar_persona_por_descripcion_vinculo,
    buscar_persona_por_codigo_vinculo,
    buscar_persona_por_nombre,
    buscar_persona_por_tipo_documento,
    buscar_persona_por_estado_detencion,
)

# ————— Wrappers LangChain —————

def make_persona_legajo_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre 'personas_legajo'.
    """

    def _buscar_persona_por_numero_documento_dni(numero_documento: str):
        return buscar_persona_por_numero_documento_dni(json_data, numero_documento)

    def _buscar_persona_por_numero_cuil(numero_cuil: str):
        return buscar_persona_por_numero_cuil(json_data, numero_cuil)

    def _buscar_persona_por_rol(rol: str):
        return buscar_persona_por_rol(json_data, rol)

    def _buscar_persona_por_descripcion_vinculo(descripcion_vinculo: str):
        return buscar_persona_por_descripcion_vinculo(json_data, descripcion_vinculo)

    def _buscar_persona_por_codigo_vinculo(codigo_vinculo: str):
        return buscar_persona_por_codigo_vinculo(json_data, codigo_vinculo)

    def _buscar_persona_por_nombre(nombre: str):
        return buscar_persona_por_nombre(json_data, nombre)

    def _buscar_persona_por_tipo_documento(tipo_documento: str):
        return buscar_persona_por_tipo_documento(json_data, tipo_documento)

    def _buscar_persona_por_estado_detencion(flag: str):
        return buscar_persona_por_estado_detencion(json_data, flag)

    return [
        LangChainTool(
            name="buscar_persona_por_numero_documento_dni",
            func=_buscar_persona_por_numero_documento_dni,
            description="Busca una persona en el legajo por su DNI (7 u 8 dígitos numéricos, escrito con o sin puntos, ej: 45.678.566)."
        ),
        LangChainTool(
            name="buscar_persona_por_numero_cuil",
            func=_buscar_persona_por_numero_cuil,
            description="Busca una persona en el legajo por su CUIL (11 dígitos numéricos, escrito con o sin puntos o dígito verificador, ej: 20-45678566-1 o 20.45678566.1)."
        ),
        LangChainTool(
            name="buscar_persona_por_rol",
            func=_buscar_persona_por_rol,
            description="Obtiene todas las personas cuyo rol coincida con la descripción indicada (ej: ACTOR, DILIGENCIANTE, DEMANDADO, etc.)."
        ),
        LangChainTool(
            name="buscar_persona_por_descripcion_vinculo",
            func=_buscar_persona_por_descripcion_vinculo,
            description="Busca personas en el legajo según la descripción de su vínculo con el expediente (ejemplo: Abogado patrocinante, Demandante, etc)."
        ),
        LangChainTool(
            name="buscar_persona_por_codigo_vinculo",
            func=_buscar_persona_por_codigo_vinculo,
            description="Busca personas cuyo vínculo esté identificado por un código único (valor numérico o alfanumérico)."
        ),
        LangChainTool(
            name="buscar_persona_por_nombre",
            func=_buscar_persona_por_nombre,
            description="Busca personas, de una manera GENERAL, por nombre, apellido o nombre completo."
        ),
        LangChainTool(
            name="buscar_persona_por_tipo_documento",
            func=_buscar_persona_por_tipo_documento,
            description="Filtra personas por tipo de documento (ej: DNI, Pasaporte, etc.)."
        ),
        LangChainTool(
            name="buscar_persona_por_estado_detencion",
            func=_buscar_persona_por_estado_detencion,
            description="Devuelve todas las personas detenidas o no detenidas (true/false, sí/no, 1/0)."
        ),
    ]
