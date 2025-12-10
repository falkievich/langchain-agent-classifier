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


def extract_relevant_fields(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae solo los campos relevantes del JSON para optimizar el procesamiento del LLM.
    
    Args:
        json_data: JSON completo del expediente
        
    Returns:
        Dict con solo los campos necesarios para extracción de personas
    """
    relevant_data = {}
    
    # Extraer personas_legajo
    if "personas_legajo" in json_data:
        personas = []
        for persona in json_data["personas_legajo"]:
            persona_filtrada = {
                "nombre_completo": persona.get("nombre_completo"),
                "rol": persona.get("rol"),
                "tipo_documento": persona.get("tipo_documento"),
                "numero_documento": persona.get("numero_documento"),
                "cuil": persona.get("cuil"),
                "fecha_nacimiento": persona.get("fecha_nacimiento"),
                "genero": persona.get("genero"),
                "es_detenido": persona.get("es_detenido")
            }
            
            # Extraer descripcion_vinculo si existe
            vinculos = persona.get("vinculos")
            if vinculos and isinstance(vinculos, dict):
                persona_filtrada["descripcion_vinculo"] = vinculos.get("descripcion_vinculo")
            
            personas.append(persona_filtrada)
        relevant_data["personas_legajo"] = personas
    
    # Extraer abogados_legajo
    if "abogados_legajo" in json_data:
        abogados = []
        for abogado in json_data["abogados_legajo"]:
            abogado_filtrado = {
                "nombre_completo": abogado.get("nombre_completo"),
                "tipo_documento": abogado.get("tipo_documento"),
                "numero_documento": abogado.get("numero_documento"),
                "cuil": abogado.get("cuil"),
                "matricula": abogado.get("matricula"),
                "representados": abogado.get("representados", [])
            }
            abogados.append(abogado_filtrado)
        relevant_data["abogados_legajo"] = abogados
    
    # Extraer funcionarios (solo nombre)
    if "funcionarios" in json_data:
        funcionarios = []
        for funcionario in json_data["funcionarios"]:
            funcionario_filtrado = {
                "nombre": funcionario.get("nombre")
            }
            funcionarios.append(funcionario_filtrado)
        relevant_data["funcionarios"] = funcionarios
    
    return relevant_data


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

    print("\n" + "="*70)
    print("SERVICIO DE EXTRACCIÓN DE PERSONAS")
    print("="*70)
    
    try:
        # Si es string, convertir a dict
        if isinstance(json_content, str):
            json_data = json.loads(json_content)
        else:
            json_data = json_content
        
        print(f"📄 JSON original recibido: {len(json.dumps(json_data))} caracteres")
        
        # Extraer solo campos relevantes
        relevant_data = extract_relevant_fields(json_data)
        json_str = json.dumps(relevant_data, indent=2, ensure_ascii=False)
        
        print(f"✂️  JSON filtrado para LLM: {len(json_str)} caracteres")
        print(f"📊 Reducción: {len(json.dumps(json_data)) - len(json_str)} caracteres (~{100 - (len(json_str)/len(json.dumps(json_data))*100):.1f}%)")
        print(f"\n📋 Secciones extraídas:")
        print(f"   - personas_legajo: {len(relevant_data.get('personas_legajo', []))} registros")
        print(f"   - abogados_legajo: {len(relevant_data.get('abogados_legajo', []))} registros")
        print(f"   - funcionarios: {len(relevant_data.get('funcionarios', []))} registros")
        
        # Obtener LLM
        llm = get_extraction_llm()
        print(f"\n🤖 Usando modelo: {llm.model}")
        
        # Preparar prompts
        system_prompt = PERSON_EXTRACTION_SYSTEM
        user_prompt = PERSON_EXTRACTION_USER_TMPL.format(json_content=json_str)
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        print(f"📝 Prompt total: {len(full_prompt)} caracteres")
        print("\n⏳ Invocando LLM para extraer personas...")
        
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
        
        print(f"\n🎯 Personas extraídas: {result['total']}")
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
