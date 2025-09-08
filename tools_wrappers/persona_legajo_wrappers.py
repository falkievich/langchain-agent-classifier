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
    buscar_persona_por_fecha_nacimiento,
    listar_todas_las_fecha_persona_participacion,
    listar_todas_las_fechas_persona_vinculos,
    buscar_persona_por_fecha_participacion,
    buscar_persona_por_fecha_vinculo,
    todas_las_personas_en_legajo,
)

from funcs.helpers_and_utility.fallback_resolvers_executor import ejecutar_con_resolver # Esta función se encarga de buscar entra todas las opciones si una función de persona_legajo_tool devuelve vacio

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
        # Tipo = "descripcion" → si no encuentra, prueba resolver_por_persona
        return ejecutar_con_resolver(json_data, buscar_persona_por_descripcion_vinculo, descripcion_vinculo, tipo="descripcion")

    def _buscar_persona_por_codigo_vinculo(codigo_vinculo: str):
        # Tipo = "codigo" → si no encuentra, prueba resolver_por_persona
        return ejecutar_con_resolver(json_data, buscar_persona_por_codigo_vinculo, codigo_vinculo, tipo="codigo")

    def _buscar_persona_por_nombre(nombre: str):
        # Tipo = "nombre" → si no encuentra, prueba resolver_por_persona
        return ejecutar_con_resolver(json_data, buscar_persona_por_nombre, nombre, tipo="nombre")

    def _buscar_persona_por_tipo_documento(tipo_documento: str):
        return buscar_persona_por_tipo_documento(json_data, tipo_documento)

    def _buscar_persona_por_estado_detencion(flag: str):
        return buscar_persona_por_estado_detencion(json_data, flag)
    
    def _buscar_persona_por_fecha_nacimiento(fecha_nacimiento: str):
        return buscar_persona_por_fecha_nacimiento(json_data, fecha_nacimiento)
    
    def _listar_todas_las_fecha_persona_participacion(_: str = ""):
        return listar_todas_las_fecha_persona_participacion(json_data)
    
    def _listar_todas_las_fechas_persona_vinculos(_: str = ""):
        return listar_todas_las_fechas_persona_vinculos(json_data)

    def _buscar_persona_por_fecha_participacion(fecha: str):
        return buscar_persona_por_fecha_participacion(json_data, fecha)

    def _buscar_persona_por_fecha_vinculo(fecha: str):
        return buscar_persona_por_fecha_vinculo(json_data, fecha)
    
    def _todas_las_personas_en_legajo(_: str = ""):
        return todas_las_personas_en_legajo(json_data)

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
        LangChainTool(
            name="buscar_persona_por_fecha_nacimiento",
            func=_buscar_persona_por_fecha_nacimiento,
            description="Devuelve la persona o personas que coincidan con la fecha de nacimiento exacta indicada. El parámetro en forma de fecha debe tener este formato: formato ISO corto: AAAA-MM-DD"
        ),
        LangChainTool(
            name="listar_todas_las_fecha_persona_participacion",
            func=_listar_todas_las_fecha_persona_participacion,
            description="Trae todas las fechas de participación/involucración, de todas las personas involucradas en el caso judicial."
        ),
        LangChainTool(
            name="listar_todas_las_fechas_persona_vinculos",
            func=_listar_todas_las_fechas_persona_vinculos,
            description="Trae todas las fechas de vinculo de todas las personas vinculadas con el expediente e involucradas en el caso judicial."
        ),
        LangChainTool(
            name="buscar_persona_por_fecha_participacion",
            func=_buscar_persona_por_fecha_participacion,
            description="Busca personas cuya fecha de participación/involucración en el caso judicial coincida con la indicada. El parámetro de fecha debe estar en formato ISO corto: AAAA-MM-DD."
        ),
        LangChainTool(
            name="buscar_persona_por_fecha_vinculo",
            func=_buscar_persona_por_fecha_vinculo,
            description="Busca personas en el legajo cuyo vínculo con el expediente haya iniciado o finalizado en la fecha indicada. El parámetro de fecha debe estar en formato ISO corto: AAAA-MM-DD."
        ),
        LangChainTool(
            name="todas_las_personas_en_legajo",
            func=_todas_las_personas_en_legajo,
            description="Trae la información de TODAS las personas involucradas en este caso, que se encuentran en el expediente/legajo."
        ),

    ]