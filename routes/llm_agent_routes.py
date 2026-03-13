from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
import json

from services.agent_service import generate_agent_response
from tools.finalizer import finalize_with_llm

router = APIRouter()


@router.post("/agent_llm")
async def process_json(
    user_prompt: str = Form(..., description="Prompt del usuario"),
    json_file: UploadFile = File(..., description="Archivo JSON del legajo"),
    format: str = Form("json", description="'json' para datos crudos, 'natural' para respuesta redactada"),
):
    """
    Endpoint principal.

    Flujo:
      1. LLM genera el plan (qué tools, en qué orden, con qué dependencias).
      2. Executor ejecuta determinísticamente las tools sobre el JSON.
      3. Si format=natural, el LLM finalizer redacta la respuesta.

    El LLM nunca accede directamente al JSON del legajo.
    """
    # 1. Leer JSON
    try:
        raw = await json_file.read()
        json_data = json.loads(raw)
        if not json_data:
            raise ValueError("El JSON está vacío o mal formado.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el JSON: {e}")

    # 2. Ejecutar pipeline
    try:
        text = await generate_agent_response(user_prompt, json_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en pipeline: {e}")

    # 3. Formato natural (opcional)
    if format.lower() == "natural":
        try:
            result = json.loads(text)
            bundle = result.get("bundle", result) if isinstance(result, dict) else result
            text = finalize_with_llm(user_prompt, bundle)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en finalizer: {e}")

    text = (text or "").replace("\r\n", "\n").strip()
    if not text.endswith("\n"):
        text += "\n"
    return PlainTextResponse(text)
