import requests
import re
import ast
from typing import Any, Dict, List

import os
from dotenv import load_dotenv

# Importar las funciones puras de tools
from Tools.abogado_tool import ALL_ABOGADO_FUNCS # Lista con todas las funciones relacionadas a los Abogados
from Tools.expediente_tool import ALL_EXPEDIENTES_FUNCS # Lista con todas las funciones relacionadas a los Expedientes
from Tools.persona_legajo_tool import ALL_PERSONAS_FUNCS # Lista con todas las funciones relacionadas a Persona Legajo
from Tools.dependencias_vistas_tool import ALL_DEPENDENCIAS_FUNCS # Lista con todas las funciones relacionadas a las Dependencias
from Tools.materia_delitos_tool import ALL_MATERIA_DELITOS_FUNCS # Lista con todas las funciones relacionadas a los delitos
from Tools.radicacion_tool import ALL_RADICACIONES_FUNCS # Lista con todas las funciones relacionadas a las radicaciones
from Tools.arrays_tool import ALL_ARRAYS_FUNCS # Lista con todas las funciones relacionadas a los arrays cortos
from funcs.langchain.langchain_resolvers_tool import (RESOLVER_AMBIGUOS_FUNCS, RESOLVER_AREA_FUNCS,) # Lista con funciones para Resolver Casos Ambiguos

from funcs.langchain.langchain_utility import normalize_and_clean # Función para normalizar los parámetros pasados a las funciones

# ------------ Cargar el archivo .env ------------ 
load_dotenv()

# ----------------- Pooles de funciones -----------------
# Base (funciones específicas por dominio)
BASE_FUNCS = (
    ALL_ABOGADO_FUNCS
    + ALL_EXPEDIENTES_FUNCS
    + ALL_PERSONAS_FUNCS
    + ALL_DEPENDENCIAS_FUNCS
    + ALL_MATERIA_DELITOS_FUNCS
    + ALL_RADICACIONES_FUNCS
    + ALL_ARRAYS_FUNCS
)

# Todas (para ejecución real y TOOLS_MAP)
ALL_FUNCS = BASE_FUNCS + RESOLVER_AMBIGUOS_FUNCS + RESOLVER_AREA_FUNCS

# ————— Configuración LLM —————
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# ————— Función GENERAL para invocar el LLM —————
def call_llm(system_msg: str, user_msg: str) -> str:
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ]
    }
    resp = requests.post(BASE_URL, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

# ————— Mapa de funciones (nombre→función) —————
TOOLS_MAP = { func.__name__: func for func in ALL_FUNCS }

# ————— Generar las firmas para el pre-prompt —————
def make_signature(f):
    args = f.__code__.co_varnames[1:f.__code__.co_argcount]
    return f"- {f.__name__}({', '.join(args)})"

SIGNATURES_BASE  = "\n".join(make_signature(f) for f in BASE_FUNCS)
SIGNATURES_AMBIG = "\n".join(make_signature(f) for f in RESOLVER_AMBIGUOS_FUNCS)
SIGNATURES_AREA  = "\n".join(make_signature(f) for f in RESOLVER_AREA_FUNCS)

# ————— Selección dinámica de invocaciones —————
def select_tools(user_prompt: str) -> List[str]:
    system_msg = (
        "Eres un agente que debe invocar una o varias funciones Python para satisfacer la petición del usuario.\n"
        "\n"
        "FUNCIONES ESPECÍFICAS (usa estas cuando el rol/tipo está claro):\n"
        f"{SIGNATURES_BASE}\n"
        "\n"
        "FUNCIONES RESOLVER — DESAMBIGUACIÓN\n"
        "(Úsalas SOLO cuando existe un VALOR CONCRETO (nombre/código/descripción/rol/estado) pero no está claro el dominio):\n"
        f"{SIGNATURES_AMBIG}\n"
        "\n"
        "FUNCIONES RESOLVER — POR ÁREA\n"
        "(Úsalas para explorar un dominio completo 1x1 cuando no conoces la función exacta):\n"
        f"{SIGNATURES_AREA}\n"
        "\n"
        "REGLAS DE USO Y FORMATO (OBLIGATORIAS):\n"
        "— Responde SOLO con llamadas válidas de funciones.\n"
        "— Usa SOLO argumentos posicionales. NO uses nombres de parámetros.\n"
        "   Correcto: resolver_por_delito('hurto agravado')\n"
        "   Incorrecto: resolver_por_delito(query='hurto agravado')\n"
        "— Si la función no requiere argumentos, invócala con paréntesis vacíos. Ej.: listar_todos_los_abogados()\n"
        "— Para múltiples valores, invoca la MISMA función varias veces, una por cada valor.\n"
        "\n"
        "ARGUMENTOS REQUERIDOS vs. FUENTES:\n"
        "— NUNCA pases literales como 'pdf', 'archivo', 'documento', 'adjunto', 'json', 'csv', 'xlsx', 'excel', "
        "'contenido del pdf', 'texto del pdf' como argumentos. Esos términos describen la FUENTE (de dónde provienen los datos), "
        "no el VALOR que consumen las funciones.\n"
        "— Si el usuario NO proporciona un argumento concreto para una búsqueda (p.ej., solo menciona un archivo), "
        "NO invoques funciones RESOLVER. En su lugar, usa la función de LISTADO del dominio.\n"
        "  Ejemplos:\n"
        "   • '¿qué delito hay en este pdf?'  ->  listar_todos_los_delitos()\n"
        "   • 'mostrame las radicaciones de este json'  ->  listar_todas_las_radicaciones_y_movimiento_expediente()\n"
        "   • 'ver dependencias en este csv'  ->  listar_todas_las_dependencias()\n"
        "\n"
        "REGLA CLAVE PARA RESOLVER_*:\n"
        "— SOLO invoca funciones RESOLVER si tienes un argumento concreto para pasar. Si no hay argumento, NO las uses.\n"
        "— Si usas funciones RESOLVER, no escribas nombres de parámetros (no 'query=...'): pasa únicamente el valor.\n"
        "\n"
        "REGLAS IDENTIFICADORES PERSONA (DNI vs CUIL):\n"
        "— Si el identificador tiene formato CUIL (con separadores o contiguo): 'NN-NNNNNNNN-N', 'NN.NNNNNNNN.N' o 11 dígitos → "
        "invoca buscar_persona_por_numero_cuil('valor').\n"
        "— Si es DNI: 7 a 9 dígitos en total, opcionalmente con puntos 'XX.XXX.XXX' → invoca "
        "buscar_persona_por_numero_documento_dni('valor').\n"
        "\n"
        "Responde SOLO con la(s) llamada(s) a función(es) válida(s), SIN numeración, SIN texto adicional."
    )
    print("user_prompt: ", user_prompt)
    print("system_msg: ", system_msg)
    raw = call_llm(system_msg, user_prompt)

    # Buscamos todas las funciones con sus paréntesis
    invocations = re.findall(r"\w+\([^)]*\)", raw)
    return invocations

# ————— Ejecutor del agente —————
def run_agent_with_tools(json_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
    """
    Ejecuta las invocaciones que devuelve el LLM, inyectando json_data
    en cada función, y combina los resultados en un único JSON.
    """
    invocations = select_tools(user_prompt)
    print("Invocaciones: ", invocations)
    results_list: List[Dict[str, Any]] = []

    for inv in invocations:
        # Parsear la llamada: func_name(arg1, arg2, ...)
        m = re.match(r"^(\w+)\((.*)\)$", inv)
        if not m:
            continue
        func_name, args_str = m.group(1), m.group(2).strip()
        func = TOOLS_MAP.get(func_name)
        if not func:
            continue

        # 1) Parsear parsed_args
        if args_str:
            try:
                parsed_args = ast.literal_eval(f"({args_str},)")
            except Exception:
                parsed_args = (args_str.strip("'\""),)
        else:
            parsed_args = ()

        # 2) Normalizar parsed_args siempre
        normalized_args = tuple(
            normalize_and_clean(str(arg))
            for arg in parsed_args
        )

        print("parsed_args sin normalizar:", parsed_args)
        print("parsed_args normalizado:", normalized_args)

        # 3) Invocar la función con el json_data y normalized_args
        try:
            result = func(json_data, *normalized_args)
            print(f"\n\nresult for {inv}: ", result)
        except Exception as e:
            result = {"error": str(e)}

        if isinstance(result, dict):
            results_list.append(result)

    # Si solo hubo una invocación, retornamos su resultado directamente
    if len(results_list) == 1:
        return results_list[0]

    # Si hay varias, combinamos manteniendo listas de valores
    aggregated: Dict[str, Any] = {}
    for res in results_list:
        for key, value in res.items():
            # inicializar lista si no existe
            if key not in aggregated:
                aggregated[key] = value if isinstance(value, list) else [value]
            else:
                # extender o agregar elemento
                if isinstance(value, list):
                    aggregated[key].extend(value)
                else:
                    aggregated[key].append(value)
    return aggregated