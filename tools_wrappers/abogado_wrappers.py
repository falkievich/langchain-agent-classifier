from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.abogado_tool import ( # Importamos las funciones "tool" de abogado
    buscar_abogado_por_nombre,
    buscar_clientes_de_abogado,
    buscar_abogados_por_cliente,
    buscar_abogado_por_matricula,
    todos_los_abogados,
    lista_todas_las_fechas_representados,
    buscar_representados_por_fecha_representacion,
)

from funcs.helpers_and_utility.fallback_resolvers_executor import ejecutar_con_resolver # Esta función se encarga de buscar entra todas las opciones si una función de abogado_tool devuelve vacio

# ————— Wrappers LangChain —————

def make_abogado_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre 'abogados'.
    Cada Tool es un wrapper alrededor de las funciones existentes,
    con fallback automático cuando corresponde.
    """

    def _buscar_abogado_por_nombre(nombre: str):
        # Tipo = "nombre" → si no encuentra, prueba resolver_por_nombre
        return ejecutar_con_resolver(json_data, buscar_abogado_por_nombre, nombre, tipo="nombre")

    def _buscar_clientes_de_abogado(nombre: str):
        return buscar_clientes_de_abogado(json_data, nombre)

    def _buscar_abogados_por_cliente(nombre: str):
        return buscar_abogados_por_cliente(json_data, nombre)

    def _buscar_abogado_por_matricula(matricula: str):
        # Tipo = "codigo" porque matrícula es alfanumérica (entra en resolver_por_codigo)
        return ejecutar_con_resolver(json_data, buscar_abogado_por_matricula, matricula, tipo="codigo")

    def _todos_los_abogados(_: str = ""):
        return todos_los_abogados(json_data)
    
    def _buscar_representados_por_fecha_representacion(fecha: str):
        return buscar_representados_por_fecha_representacion(json_data, fecha)
    
    def _lista_todas_las_fechas_representados(_: str = ""):
        return lista_todas_las_fechas_representados(json_data)

    # ——— Registrar todas como Tools ———
    return [
        LangChainTool(
            name="buscar_abogado_por_nombre",
            func=_buscar_abogado_por_nombre,
            description="Busca toda la información de un abogado en base a su nombre completo, apellido o nombre."
        ),
        LangChainTool(
            name="buscar_clientes_de_abogado",
            func=_buscar_clientes_de_abogado,
            description="Devuelve la lista de personas que representa un abogado dado a su nombre completo, apellido o nombre."
        ),
        LangChainTool(
            name="buscar_abogados_por_cliente",
            func=_buscar_abogados_por_cliente,
            description="Devuelve todos los abogados que representan a un cliente dado su nombre completo, apellido o nombre."
        ),
        LangChainTool(
            name="buscar_abogado_por_matricula",
            func=_buscar_abogado_por_matricula,
            description="Busca un abogado utilizando su número de matrícula (este SERÁ alfanumérico)."
        ),
        LangChainTool(
            name="todos_los_abogados",
            func=_todos_los_abogados,
            description="Lista todos los abogados del legajo con toda la informacion disponible en el PDF, JSON, Archivo, Documento, CSV."
        ),
        LangChainTool(
            name="buscar_representados_por_fecha_representacion",
            func=_buscar_representados_por_fecha_representacion,
            description="Busca representados en base a UNA, devolviendo la fecha en que comenzaron a ser representados por un abogado o la fecha en que dejaron de serlo. El parámetro de fecha debe estar en formato ISO corto: AAAA-MM-DD."
        ),
        LangChainTool(
            name="lista_todas_las_fechas_representados",
            func=_lista_todas_las_fechas_representados,
            description="Trae todas las fechas de representación de las personas representadas por los abogados"
        ),
    ]
