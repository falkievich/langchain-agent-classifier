from typing import Any, Dict
from langchain.agents import Tool as LangChainTool 

from langchain_tools.abogado_tool import ( # Importamos las funciones "tool" de abogado
    buscar_abogado_por_nombre,
    buscar_clientes_de_abogado,
    buscar_abogados_por_cliente,
    buscar_abogado_por_matricula,
    todos_los_abogados,
)

# ————— Wrappers LangChain —————

def make_abogado_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar sobre 'abogados'.
    Cada Tool es un wrapper alrededor de las funciones existentes.
    """

    def _buscar_abogado_por_nombre(nombre: str):
        return buscar_abogado_por_nombre(json_data, nombre)

    def _buscar_clientes_de_abogado(nombre: str):
        return buscar_clientes_de_abogado(json_data, nombre)

    def _buscar_abogados_por_cliente(nombre: str):
        return buscar_abogados_por_cliente(json_data, nombre)

    def _buscar_abogado_por_matricula(matricula: str):
        return buscar_abogado_por_matricula(json_data, matricula)

    def _todos_los_abogados(_: str = ""):
        return todos_los_abogados(json_data)

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
    ]
