from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import json

# Importar la función orquestadora del agente
from funcs.langchain.langchain_agent import run_agent_with_tools


#---------------------------------------------------------- Router
router = APIRouter()

# ---------------------------------------------------------- Post - Cargar un archivo JSON y procesar prompt
@router.post("/agent_llm")
async def process_json(
    user_prompt: str = Form(..., description="Prompt del usuario"),
    json_file: UploadFile = File(..., description="Archivo JSON de entrada")
):
    """
    Endpoint que recibe un JSON y un prompt, y delega toda la lógica al agente.
    """
    # Leer y parsear JSON
    try:
        raw = await json_file.read()
        json_data = json.loads(raw)
        if not json_data:
            raise HTTPException(status_code=400, detail="El JSON está vacío o mal formado.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el JSON: {e}")

    # Ejecutar el agente, que ya incluye la selección de tools y el LLM
    try:
        res = run_agent_with_tools(json_data, user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar el agente: {e}")

    # El agente suele devolver dict con "output"; si no, casteamos a str
    text = res.get("output") if isinstance(res, dict) else str(res)
    text = (text or "").replace("\r\n", "\n").strip()
    if not text.endswith("\n"):
        text += "\n"

    return PlainTextResponse(text)
