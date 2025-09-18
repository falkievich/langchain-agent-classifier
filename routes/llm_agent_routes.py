from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
import json

from services.agent_service import generate_agent_response # Importar la función orquestadora del agente

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
    # 1) Leer JSON
    try:
        raw = await json_file.read()
        json_data = json.loads(raw)
        if not json_data:
            raise ValueError("El JSON está vacío o mal formado.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el JSON: {e}")

    # 2) Delegar al servicio
    try:
        text = await generate_agent_response(user_prompt, json_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en pipeline: {e}")

    # 3) Normalizar y responder
    text = (text or "").replace("\r\n", "\n").strip()
    if not text.endswith("\n"):
        text += "\n"
    return PlainTextResponse(text)