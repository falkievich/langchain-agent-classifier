from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json

from services.agent_service import generate_agent_response


router = APIRouter()


@router.post("/agent_llm")
async def process_json(
    user_prompt: str = Form(..., description="Prompt del usuario"),
    json_file: UploadFile = File(..., description="Archivo JSON del legajo"),
):
    """
    Endpoint principal.

    Flujo:
      1. LLM genera el plan (qué tools, en qué orden, con qué dependencias).
      2. Executor ejecuta determinísticamente las tools sobre el JSON.

    La respuesta SIEMPRE se devuelve en formato JSON.
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

    # 3. Siempre devolver JSON
    try:
        parsed = json.loads(text) if isinstance(text, str) else text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Respuesta del pipeline no es JSON válido: {e}")

    return JSONResponse(content=parsed)
