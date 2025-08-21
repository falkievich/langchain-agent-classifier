from typing import Any, Dict

from dotenv import load_dotenv

from langchain.agents import initialize_agent, AgentType
from langchain.schema import SystemMessage

# LLM custom
from classes.custom_llm_classes import CustomOpenWebLLM

# Importar tools wrappers
from tools_wrappers.abogado_wrappers import make_abogado_tools
from tools_wrappers.expediente_wrappers import make_expediente_tools
from tools_wrappers.persona_legajo_wrappers import make_persona_legajo_tools
from tools_wrappers.dependencias_wrappers import make_dependencias_tools
from tools_wrappers.materia_delitos_wrappers import make_materia_delitos_tools
from tools_wrappers.radicacion_wrappers import make_radicacion_tools
from tools_wrappers.arrays_wrappers import make_arrays_tools

# Resolver tools
# from funcs.langchain.langchain_resolvers_tool import (
#     make_resolver_ambiguos_tools,
#     make_resolver_area_tools,
# )

# ------------ Cargar el archivo .env ------------ 
load_dotenv()

# ----------------- LLM -----------------
llm = CustomOpenWebLLM()

# ----------------- Prefix (antes era system_msg en select_tools) -----------------
AGENT_PREFIX = """
Eres un agente que debe invocar una o varias funciones Python para satisfacer la petición del usuario.

REGLAS DE USO Y FORMATO (OBLIGATORIAS):
— Responde SOLO con llamadas válidas de funciones.
— Usa SOLO argumentos posicionales. NO uses nombres de parámetros.
   Correcto: resolver_por_delito('hurto agravado')
   Incorrecto: resolver_por_delito(query='hurto agravado')
— Si la función no requiere argumentos, invócala con paréntesis vacíos. Ej.: listar_todos_los_abogados()
— Para múltiples valores, invoca la MISMA función varias veces, una por cada valor.

ARGUMENTOS REQUERIDOS vs. FUENTES:
— NUNCA pases literales como 'pdf', 'archivo', 'documento', 'adjunto', 'json', 'csv', 'xlsx', 'excel',
'contenido del pdf', 'texto del pdf' como argumentos. Esos términos describen la FUENTE (de dónde provienen los datos),
no el VALOR que consumen las funciones.
— Si el usuario NO proporciona un argumento concreto para una búsqueda (p.ej., solo menciona un archivo),
usa la función de LISTADO del dominio.
  Ejemplos:
   • '¿qué delito hay en este pdf?'  ->  listar_todos_los_delitos()
   • 'mostrame las radicaciones de este json'  ->  listar_todas_las_radicaciones_y_movimiento_expediente()
   • 'ver dependencias en este csv'  ->  listar_todas_las_dependencias()
"""

# ----------------- Prefix -----------------
AGENT_PREFIX = """ ... """   # <-- lo de mi prompt

# ----------------- Ejecutor -----------------
def run_agent_with_tools(json_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
    """
    Ejecuta el agente con las Tools y devuelve el resultado en JSON.
    """
    print("Prompt del usuario: ",user_prompt)
    tools = (
        make_abogado_tools(json_data)
        + make_expediente_tools(json_data)
        + make_persona_legajo_tools(json_data)
        + make_dependencias_tools(json_data)
        + make_materia_delitos_tools(json_data)
        + make_radicacion_tools(json_data)
        + make_arrays_tools(json_data)
        #+ make_resolver_ambiguos_tools(json_data)
        #+ make_resolver_area_tools(json_data)
    )

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        agent_kwargs={"extra_prompt_messages": [SystemMessage(content=AGENT_PREFIX)]},
    )

    return agent.invoke(user_prompt)
