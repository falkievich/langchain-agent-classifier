from funcs.helpers_and_utility.langchain_utility import  buscar_entradas_en_lista, extraer_campos_en_lista # Importamos las utilidades
from typing import Any, Dict, List

# ————— Herramientas (Tools) para extracción en el JSON —————
#------------------------------------------------------------------------- (saqué ids) Lista todos los abogados
def todos_los_abogados(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Lista todos los abogados con su nombre completo y matrícula."""
    abogados = json_data.get("abogados_legajo", [])
    listado: List[Dict[str, Any]] = []

    for a in abogados:
        # Excluir IDs de nivel superior
        detalle = {k: v for k, v in a.items() if k not in ("abogado_id", "abogado_persona_id")}
        # Limpiar los representados: excluir persona_id
        reps = detalle.get("representados", [])
        detalle["representados"] = [
            {k: v for k, v in rep.items() if k != "persona_id"}
            for rep in reps
        ]
        listado.append(detalle)

    return {"abogados": listado}

#-------------------------------------------------------------------------  Busca un abogado por nombre y, si lo encuentra, trae también la persona vinculada.
def buscar_abogado_por_nombre(json_data: Dict[str, Any], nombre_abogado: str) -> Dict[str, Any]:
    """Busca TODA la información de un abogado en base a su nombre."""
    resultado: Dict[str, Any] = {}

    # 1) Abogados que matchean por nombre/apellido/nombre_completo (match exacto)
    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="abogados_legajo",
        fields=["nombre", "apellido", "nombre_completo"],
        needle=nombre_abogado,
        exact=True,
    )
    if matches:
        resultado["abogados_legajo"] = matches

        # 2) Personas relacionadas por abogado_persona_id
        personas = json_data.get("personas_legajo", []) or []
        persona_ids = {a.get("abogado_persona_id") for a in matches if a.get("abogado_persona_id")}
        related = [p for p in personas if p.get("persona_id") in persona_ids]
        if related:
            resultado["personas_legajo"] = related

    return resultado

#------------------------------------------------------------------------- (saqué ids) Busca un abogado por nombre y devuelve solo la lista de clientes que representa.
def buscar_clientes_de_abogado(json_data: Dict[str, Any], nombre_abogado: str) -> Dict[str, Any]:
    """Devuelve la lista de personas que el abogado con ese nombre representa."""
    # Buscar el/los abogados
    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="abogados_legajo",
        fields=["nombre", "apellido", "nombre_completo"],
        needle=nombre_abogado,
        exact=True
    )

    # Si no hay coincidencias, lista vacía
    if not matches:
        return {"representados": []}

    # Unir todas las listas de 'representados' de los abogados coincidentes
    representados: List[Dict[str, Any]] = []
    for a in matches:
        reps = a.get("representados", []) or []
        representados.extend(reps)

    return {"representados": representados}

#------------------------------------------------------------------------- (SACAR IDS) Busca todos los abogados que representan a un cliente dado por nombre.
def buscar_abogados_por_cliente(json_data: Dict[str, Any], nombre_cliente: str) -> Dict[str, Any]:
    """Devuelve todos los abogados que representan al cliente dado."""
    resultado: Dict[str, Any] = {}

    # 1) Matchear el/los clientes por nombre/apellido/nombre_completo (match exacto)
    matches_p = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="personas_legajo",
        fields=["nombre", "apellido", "nombre_completo"],
        needle=nombre_cliente,
        exact=True,
    )
    if not matches_p:
        return resultado

    cliente_ids = {p.get("persona_id") for p in matches_p if p.get("persona_id")}

    # 2) Buscar abogados que tengan a esos persona_id dentro de 'representados'
    abogados = json_data.get("abogados_legajo", []) or []
    reps: List[Dict[str, Any]] = []
    for a in abogados:
        for rep in a.get("representados", []) or []:
            if rep.get("persona_id") in cliente_ids:
                reps.append(a)
                break

    if reps:
        resultado["abogados_por_cliente"] = reps

    return resultado

#------------------------------------------------------------------------- Busca abogados filtrando por número de matrícula
def buscar_abogado_por_matricula(json_data: Dict[str, Any], numero_matricula: str) -> Any:
    """
    Busca abogados por número de matrícula, permitiendo coincidencias parciales
    """

    matches = buscar_entradas_en_lista(
        json_data=json_data,
        list_key="abogados_legajo",
        fields=["matricula"],
        needle=numero_matricula,
        exact=False
    )

    return {"abogado_por_matricula": matches}

#------------------------------------------------------------------------- Traer todas las fechas de representación
def lista_todas_las_fechas_representados(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve todas las fechas (fecha_desde, fecha_hasta) de todos los representados
    dentro de abogados_legajo.
    """
    filas = extraer_campos_en_lista(
        json_data,
        "abogados_legajo.representados",
        [
            "fecha_desde",
            "fecha_hasta",
            ("nombre_completo", "representado_nombre_completo"),
            ("^.nombre_completo", "abogado_nombre_completo"),
        ],
    )
    return {"todas_las_fechas_representados": filas}

#-------------------------------------------------------------------------  Devuelve representados por fecha de inicio o fin de la representación
def buscar_representados_por_fecha_representacion(json_data: Dict[str, Any], fecha: str) -> Dict[str, Any]:
    """
    Busca representados dentro de abogados_legajo en función de la fecha indicada:
    - representados.fecha_desde: Fecha de inicio de la representación.
    - representados.fecha_hasta: Fecha de fin de la representación.
    """
    matches = buscar_entradas_en_lista(
        json_data,
        list_key="abogados_legajo",
        fields=["representados.fecha_desde", "representados.fecha_hasta"],
        needle=fecha,
        exact=False
    )
    if matches:
        return {"representados_por_fecha_representacion": matches}
    else:
        return lista_todas_las_fechas_representados(json_data)

#------------------------------------------------------------------------- Lista con todas las funciones de relacioanda a los Abogados
ALL_ABOGADO_FUNCS = [
    todos_los_abogados,
    buscar_abogado_por_nombre,
    buscar_clientes_de_abogado,
    buscar_abogados_por_cliente,
    buscar_abogado_por_matricula,
    lista_todas_las_fechas_representados,
    buscar_representados_por_fecha_representacion,
]