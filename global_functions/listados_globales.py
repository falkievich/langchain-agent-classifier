from typing import Any, Dict
# Importamos las funciones de cada dominio
from langchain_tools.abogado_tool import todos_los_abogados
from langchain_tools.persona_legajo_tool import todas_las_personas_en_legajo
from langchain_tools.dependencias_vistas_tool import listar_todas_las_dependencias
from langchain_tools.materia_delitos_tool import listar_todos_los_delitos
from langchain_tools.radicacion_tool import listar_todas_las_radicaciones_y_movimiento_expediente
from langchain_tools.expediente_tool import obtener_info_general_expediente
from langchain_tools.arrays_tool import listar_todos_los_funcionarios, listar_todas_las_causas, listar_todas_las_clasificaciones_legajo

# Lista de dominios soportados por listar_todo
LISTAR_DOMINIOS_DISPONIBLES = [
    "abogados: Lista todos los abogados registrados en el legajo con sus datos completos y vinculaciones relevantes.",
    "personas: Lista todas las personas involucradas en el expediente o legajo, incluyendo todas sus participaciones y vínculos.",
    "dependencias: Lista todas las dependencias y organismos asociados al legajo, con su estructura jerárquica y roles funcionales.",
    "delitos: Lista todos los delitos relacionados con el legajo, incluyendo su clasificación y orden de registro.",
    "funcionarios: Lista todos los funcionarios intervinientes o asociados al legajo con la información disponible.",
    "causas: Lista todas las causas judiciales registradas dentro del legajo con sus características principales.",
    "clasificaciones: Lista todas las clasificaciones o categorías del legajo que definen su tipo o naturaleza.",
    "radicaciones: Lista todas las radicaciones y movimientos del expediente entre los distintos organismos intervinientes.",
    "expediente: Devuelve toda la información general y estructural del expediente, incluyendo su estado y contexto procesal.",
]

def listar_todo(json_data: Dict[str, Any], dominio: str) -> Dict[str, Any]:
    """
    Devuelve toda la información de un dominio específico.

    Dominios disponibles: LISTAR_DOMINIOS_DISPONIBLES
    """
    if dominio == "abogados":
        return todos_los_abogados(json_data)
    elif dominio == "personas":
        return todas_las_personas_en_legajo(json_data)
    elif dominio == "dependencias":
        return listar_todas_las_dependencias(json_data)
    elif dominio == "delitos":
        return listar_todos_los_delitos(json_data)
    elif dominio == "funcionarios":
        return listar_todos_los_funcionarios(json_data)
    elif dominio == "causas":
        return listar_todas_las_causas(json_data)
    elif dominio == "clasificaciones":
        return listar_todas_las_clasificaciones_legajo(json_data)
    elif dominio == "radicaciones":
        return listar_todas_las_radicaciones_y_movimiento_expediente(json_data)
    elif dominio == "expediente":
        return obtener_info_general_expediente(json_data)
    else:
        return {"error": f"Dominio '{dominio}' no reconocido en listar_todo. Opciones válidas: {LISTAR_DOMINIOS_DISPONIBLES}"}
