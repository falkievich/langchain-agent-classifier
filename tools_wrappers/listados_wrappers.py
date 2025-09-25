from typing import Dict, Any
from langchain.agents import Tool as LangChainTool
from global_functions.listados_globales import listar_todo, LISTAR_DOMINIOS_DISPONIBLES


def make_listados_tools(json_data: Dict[str, Any]):
    """
    Devuelve la lista de Tools de LangChain para operar con listados globales.
    Actualmente expone listar_todo(dominio).
    """
    return [
        LangChainTool(
            name="listar_todo",
            func=lambda dominio: listar_todo(json_data, dominio),
            description=f"Lista toda la información de un dominio específico. "
                        f"Dominios disponibles: {LISTAR_DOMINIOS_DISPONIBLES}"
        )
    ]
