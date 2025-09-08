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

# ------------ Cargar el archivo .env ------------ 
load_dotenv()

# ----------------- LLM -----------------
llm = CustomOpenWebLLM()

# ----------------- Prefix (antes era system_msg en select_tools) -----------------
AGENT_PREFIX = """
Eres un agente que debe invocar una o varias funciones Python para satisfacer la petición del usuario.

REGLAS DE USO Y FORMATO (OBLIGATORIAS):
— Responde SOLO con llamadas válidas de funciones.
— Usa SOLO argumentos posicionales. NO uses nombres de parámetros en ningún caso.
   Correcto: buscar_abogados_por_cliente("José López")
   Incorrecto: buscar_abogados_por_cliente(nombre="José López")
   Incorrecto: buscar_abogados_por_cliente(query="José López")
— Si la función no requiere argumentos, invócala con paréntesis vacíos.
   Ejemplo: listar_todos_los_abogados()
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

FORMATO DE FECHAS (OBLIGATORIO):
— Siempre convierte cualquier fecha que mencione el usuario al formato ISO corto: AAAA-MM-DD.
   Ejemplos:
   • '21.03.2025'  ->  '2025-03-21'
   • '21/03/2025'  ->  '2025-03-21'
   • '21 de marzo de 2025'  ->  '2025-03-21'
   • 'marzo 21 2025'  ->  '2025-03-21'
— Si la fecha incluye hora o zona horaria, IGNÓRALA y conserva solo AAAA-MM-DD.

RESPUESTA FINAL:
— La Final Answer siempre debe estar redactada en ESPAÑOL.
— La Final Answer no debe mencionar ni mostrar los nombres de las funciones utilizadas.
"""

# ----------------- Prefix -----------------
AGENT_PREFIX = """ ... """   # Preprompt

# ----------------- Ejecutor -----------------
def run_agent_with_tools(json_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
    """
    Ejecuta el agente con las Tools y devuelve el resultado en JSON.
    """
    print("\n==================== NUEVA EJECUCIÓN ====================")
    print("Prompt del usuario:", user_prompt)
    print("----------------------------------------------------------")

    # Construir Tools dinámicamente
    tools = (
        make_abogado_tools(json_data)
        + make_expediente_tools(json_data)
        + make_persona_legajo_tools(json_data)
        + make_dependencias_tools(json_data)
        + make_materia_delitos_tools(json_data)
        + make_radicacion_tools(json_data)
        + make_arrays_tools(json_data)
    )

    # 🔹 Mostrar lista de Tools que recibe el LLM
    print("\n--- TOOLS DISPONIBLES ---")
    for tool in tools:
        print(f"→ {tool.name}: {tool.description}")

    print("==========================================================\n")

    # Construcción del agente
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        agent_kwargs={"extra_prompt_messages": [SystemMessage(content=AGENT_PREFIX)]},
        handle_parsing_errors=True,  # Si captura error, lo envia al LLM para que lo corrija
    )

    return agent.invoke(user_prompt)
