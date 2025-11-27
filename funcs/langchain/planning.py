import json, re
from pydantic import ValidationError

# -------- Importaciones --------
# CustomOpenWebLLM: wrapper del LLM para invocar el modelo.
from classes.custom_llm_classes import CustomOpenWebLLM

# Plan: esquema Pydantic que define el contrato del Planner (lista de calls).
from schema.call_and_plan_schema import Plan

# PLANNER_SYSTEM_TPL / PLANNER_USER_TMPL: prompts del Planner (system + user).
# MAX_CALLS: límite de cantidad de llamadas permitidas en el plan.
from funcs.langchain.core import PLANNER_SYSTEM_TPL, PLANNER_USER_TMPL, MAX_CALLS


# -------- Planner --------
# Esta sección construye el "plan" de ejecución:
# - Formatea el listado de tools para el prompt.
# - Llama al LLM con un system + user que exigen JSON estricto.
# - Recorta defensivamente el JSON, lo valida con Pydantic y aplica reglas:
#   * Tools válidas (presentes en allowed_tools)
#   * Límite de llamadas (MAX_CALLS)
# Devuelve un objeto Plan listo para ser ejecutado en paralelo.

def _parse_function_calls(raw: str) -> list:
    """
    Convierte salida estilo funcion:
        buscar_persona("rol", "Demandante")
        listar_todo("expediente")
    en lista de dicts [{tool, args}, ...].
    
    También intenta parsear si el modelo devuelve JSON con formato alternativo.
    """
    calls = []
    
    print(f"\n🔍 Parseando raw output (length: {len(raw)} chars)")
    print(f"🔍 Primeros 200 chars: {raw[:200]}")
    print(f"🔍 Últimos 200 chars: {raw[-200:]}")
    
    # Intento 1: Parsear como JSON si el raw parece ser JSON
    raw_stripped = raw.strip()
    
    # Limpiar posibles escapes dobles
    if '\\"' in raw_stripped:
        print(f"⚠️ Detectadas comillas escapadas dobles, intentando limpiar...")
        raw_stripped = raw_stripped.replace('\\"', '"')
    
    # Intentar extraer JSON si está entre texto
    json_match = re.search(r'\{.*\}', raw_stripped, re.DOTALL)
    if json_match:
        json_candidate = json_match.group(0)
        print(f"🔍 JSON candidato encontrado (length: {len(json_candidate)})")
        print(f"🔍 JSON candidato preview: {json_candidate[:300]}")
        try:
            data = json.loads(json_candidate)
            print(f"🔍 JSON parseado exitosamente. Type: {type(data)}")
            if isinstance(data, dict):
                print(f"🔍 Keys: {list(data.keys())}")
            else:
                print(f"🔍 Es una lista con {len(data)} elementos")
            
            # Formato: {"steps": [{"action": "...", "params": [...]}]}
            if isinstance(data, dict) and "steps" in data:
                print(f"🔍 Formato detectado: steps (count: {len(data['steps'])})")
                for step in data["steps"]:
                    tool = step.get("action", "")
                    args = step.get("params", [])
                    print(f"   - {tool}({args})")
                    calls.append({"tool": tool, "args": args})
                return calls
            
            # Formato: {"calls": [{"tool": "...", "args": [...]}]}
            if isinstance(data, dict) and "calls" in data:
                print(f"🔍 Formato detectado: calls (count: {len(data['calls'])})")
                for call in data["calls"]:
                    print(f"   - {call}")
                    calls.append(call)
                return calls
            
            # Formato: [{"tool": "...", "args": [...]}]
            if isinstance(data, list):
                print(f"🔍 Formato detectado: lista directa (count: {len(data)})")
                return data
            
            print(f"⚠️ JSON parseado pero formato no reconocido. Data: {data}")
                
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parseando JSON: {e}")
    
    # Intento 2: Parsear como llamadas de función línea por línea
    print(f"🔍 Intentando parsear como llamadas de función...")
    lines_processed = 0
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        match = re.match(r"(\w+)\((.*)\)", line)
        if not match:
            continue
        lines_processed += 1
        tool = match.group(1)
        args_str = match.group(2).strip()
        if not args_str:
            args = []
        else:
            # separar por comas, limpiar comillas
            args = [a.strip().strip('"').strip("'") for a in args_str.split(",")]
        print(f"   - Línea parseada: {tool}({args})")
        calls.append({"tool": tool, "args": args})
    
    print(f"🔍 Total líneas procesadas: {lines_processed}, calls encontradas: {len(calls)}")
    return calls

def build_tools_bullets(allowed_tools) -> str:
    """Convierte la lista de tools en bullets resumidos para el prompt del Planner."""
    summarized = [{"name": t.name, "description": t.description} for t in allowed_tools]
    return "\n".join(f"- {t['name']}: {t['description']}" for t in summarized)

def run_planner(llm: CustomOpenWebLLM, user_prompt: str, allowed_tools, max_calls: int = MAX_CALLS) -> Plan:
    """Invoca al Planner (LLM) para obtener un plan JSON y lo valida."""

    # 1) Preparar prompts (system + user) con reglas y listado de tools
    system = PLANNER_SYSTEM_TPL.substitute(max_calls=max_calls)
    tools_bullets = build_tools_bullets(allowed_tools)
    
    # Usar replace() en lugar de format() para evitar problemas con llaves {} en el contenido
    user = PLANNER_USER_TMPL.replace("{user_prompt}", user_prompt).replace("{tools_bullets}", tools_bullets)

    # 2) Llamar al LLM (una sola vez) para que devuelva SOLO JSON
    raw = llm._call(prompt=f"{system}\n\n{user}", stop=None)

    print("\n=== RAW OUTPUT DEL PLANNER ===")
    print(raw)
    print("==============================\n")

    # 3) Parsear salida (función o JSON) y validar con Pydantic Plan
    try:
        calls_data = _parse_function_calls(raw)
        print(f"=== CALLS PARSEADAS: {len(calls_data)} ===")
        for i, call in enumerate(calls_data):
            if isinstance(call, dict) and "tool" in call and "args" in call:
                args_repr = ', '.join(repr(a) for a in call['args'])
                print(f"  {i+1}. {call['tool']}({args_repr})")
            else:
                print(f"  {i+1}. [FORMATO INESPERADO]: {call}")
        print()
        
        plan = Plan(calls=calls_data)
    except ValidationError as e:
        print(f"❌ Error de validación Pydantic: {e}")
        print(f"❌ Calls data recibidas: {calls_data}")
        raise RuntimeError(f"Planner devolvió formato inválido: {e}\nRAW:\n{raw}")
    except Exception as e:
        print(f"❌ Error inesperado parseando plan: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Error parseando plan: {e}\nRAW:\n{raw}")

    # 5) Validaciones de negocio (tools permitidas + tope de llamadas)
    allowed_names = {t.name for t in allowed_tools}
    for c in plan.calls:
        if c.tool not in allowed_names:
            raise RuntimeError(f"Tool no permitida en plan: {c.tool}")

    if len(plan.calls) > max_calls:
        plan.calls = plan.calls[:max_calls]

    return plan

# -------- Registry --------
# Esta sección crea el "registry" (diccionario) que mapea nombre de tool → callable:
# - Soporta tools con .func (callable Python)
# - Soporta Runnables con .invoke (se envuelven como función)
# El registry es lo que usa el ejecutor para disparar cada call del plan.


def build_registry(tools):
    """Construye {nombre_tool: callable} desde la lista de tools de LangChain."""
    registry = {}
    for t in tools:
        if hasattr(t, "func") and callable(getattr(t, "func")):
            registry[t.name] = t.func
        elif hasattr(t, "invoke") and callable(getattr(t, "invoke")):
            # Envolvemos el Runnable para poder llamarlo como función normal
            def make_invoke(tt):
                def _call(*args, **kwargs):
                    return tt.invoke(*args, **kwargs)
                return _call
            registry[t.name] = make_invoke(t)
        else:
            raise RuntimeError(f"No sé cómo ejecutar la tool: {t.name}")
    return registry
