import json
import os
from typing import Any, Dict, Union
from dotenv import load_dotenv
from classes.custom_llm_classes import CustomOpenWebLLM
from funcs.langchain.core import PERSON_EXTRACTION_SYSTEM, PERSON_EXTRACTION_USER_TMPL

load_dotenv()

def get_extraction_llm() -> CustomOpenWebLLM:
    """Crea una instancia del LLM usando MODEL_ID_2 para extracción de personas."""
    model_id_2 = os.getenv("MODEL_ID_2")
    if not model_id_2:
        raise ValueError("MODEL_ID_2 no está configurado en el archivo .env")
    
    # Crear instancia del LLM con el modelo alternativo
    llm = CustomOpenWebLLM()
    llm.model = model_id_2
    return llm


def extract_persons_from_json(json_content: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extrae todas las personas mencionadas en un JSON usando LLM.
    
    Args:
        json_content: JSON como string o diccionario
        
    Returns:
        Dict con formato:
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

    print("\nSERVICIO DE EXTRACCIÓN DE PERSONAS")
    
    try:
        # Si es dict, convertir a JSON string formateado
        if isinstance(json_content, dict):
            json_str = json.dumps(json_content, indent=2, ensure_ascii=False)
        else:
            json_str = json_content
            # Validar que sea JSON válido
            json.loads(json_str)
        
        print(f"JSON recibido: {len(json_str)} caracteres")
        
        # Obtener LLM
        llm = get_extraction_llm()
        print(f"Usando modelo: {llm.model}")
        
        # Preparar prompts
        system_prompt = PERSON_EXTRACTION_SYSTEM
        user_prompt = PERSON_EXTRACTION_USER_TMPL.format(json_content=json_str)
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        print(f"Prompt total: {len(full_prompt)} caracteres")
        print("\nInvocando LLM para extraer personas...")
        
        # Llamar al LLM
        raw_response = llm._call(prompt=full_prompt, stop=None)
        
        print(f"✅ Respuesta recibida: {len(raw_response)} caracteres")
        
        # Limpiar y extraer JSON de la respuesta
        json_str_clean = raw_response.strip()
        
        # Buscar JSON en la respuesta (por si hay texto adicional)
        if not json_str_clean.startswith("{"):
            start = json_str_clean.find("{")
            end = json_str_clean.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str_clean = json_str_clean[start:end+1]
        
        # Parsear respuesta
        result = json.loads(json_str_clean)
        
        # Validar estructura
        if "personas" not in result:
            result = {"personas": [], "total": 0}
        
        if "total" not in result:
            result["total"] = len(result.get("personas", []))
        
        print(f"✅ Personas extraídas: {result['total']}")
        print("="*70 + "\n")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON: {e}")
        return {
            "error": f"JSON inválido: {str(e)}",
            "personas": [],
            "total": 0
        }
    except Exception as e:
        print(f"❌ Error en extracción: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error en extracción: {str(e)}",
            "personas": [],
            "total": 0
        }
