from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
import json
import traceback
from services.person_extraction_service import extract_persons_from_json

#---------------------------------------------------------- Router
# Crear router de FastAPI
router = APIRouter()

# ---------------------------------------------------------- Post - Obtener Personas de un JSON mediante el uso de un LLM
@router.post("/extract-persons-with-llm")
async def extract_persons(
    json_txt_file: UploadFile = File(..., description="Archivo JSON/TXT de entrada")
):
    """
    Endpoint que recibe un archivo JSON/TXT y extrae todas las personas mencionadas usando LLM.
    
    Parámetros:
    - json_txt_file: Archivo JSON o TXT que contiene el expediente judicial
    
    Retorna:
    {
        "personas": [
            {
                "nombre": "Nombre Completo",
                "rol": "Rol en el expediente",
                "datos_adicionales": {...}
            }
        ],
        "total": int
    }
    """
    # 1) Leer el archivo
    try:
        raw = await json_txt_file.read()
        json_data = json.loads(raw)
        if not json_data:
            raise ValueError("El archivo está vacío o mal formado.")
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error al leer el JSON: archivo inválido o mal formado. {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error al leer el archivo: {str(e)}"
        )
    
    # 2) Llamar al servicio de extracción (envía el JSON completo al LLM con el preprompt)
    try:
        result = extract_persons_from_json(json_data)
    except Exception as e:
        print(f"❌ Error en endpoint extract-persons: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error en pipeline de extracción: {str(e)}"
        )
    
    # 3) Verificar si hubo error en el resultado
    if "error" in result and result.get("total", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )
    
    return result

# ---------------------------------------------------------- Get - Verificar que el servicio de extracción de personas esté disponible y operativo
@router.get("/extract-persons/health")
async def health_check():
    """Health check del servicio de extracción de personas."""
    return {
        "status": "ok",
        "service": "person_extraction",
        "endpoint": "/extract-persons"
    }
