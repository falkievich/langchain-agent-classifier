from typing import Any, Dict, List, Union

# === MAPEOS DE DOMINIOS A CLAVES JSON ===
DOMINIO_MAPEO = {
    "abogados": "abogados_legajo",
    "personas": "personas_legajo",
    "dependencias": "dependencias_vistas",
    "delitos": "materia_delitos",
    "radicaciones": "radicaciones",
    "expediente": "cabecera_legajo",
}

# === CAMPOS PRIORITARIOS Y EXCLUIDOS ===
PRIORIDAD_CAMPOS = ["nombre", "matricula", "dni", "cliente", "abogado", "causa", "fecha"]
EXCLUIR_PATHS = ["metadata", "raw_text", "documentos"]
MAX_DEPTH = 5


def _deep_search_dominio(
    obj: Union[Dict, List],
    needle: str,
    path: str = "",
    parent: Any = None,
    depth: int = 0,
) -> List[Dict[str, Any]]:
    """Búsqueda recursiva dentro del dominio seleccionado."""
    results = []
    if depth > MAX_DEPTH:
        return results

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if any(ex in new_path for ex in EXCLUIR_PATHS):
                continue

            if isinstance(v, (dict, list)):
                results.extend(
                    _deep_search_dominio(v, needle, new_path, parent=v, depth=depth + 1)
                )
            else:
                try:
                    if needle.lower() in str(v).lower():
                        prioridad = 0
                        if any(p in new_path.lower() for p in PRIORIDAD_CAMPOS):
                            prioridad += 2
                        if isinstance(v, str) and len(v) < 40:
                            prioridad += 1
                        results.append({
                            "path": new_path,
                            "value": v,
                            "full_entry": parent if parent is not None else obj,
                            "prioridad": prioridad
                        })
                except Exception:
                    pass

    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            new_path = f"{path}[{idx}]"
            if isinstance(v, (dict, list)):
                results.extend(
                    _deep_search_dominio(v, needle, new_path, parent=v, depth=depth + 1)
                )
            else:
                try:
                    if needle.lower() in str(v).lower():
                        results.append({
                            "path": new_path,
                            "value": v,
                            "full_entry": parent if parent is not None else v,
                            "prioridad": 0
                        })
                except Exception:
                    pass

    return results


def buscar_en_json_por_dominio(
    json_data: Dict[str, Any],
    dominio: str,
    query: str
) -> Dict[str, Any]:
    """
    Busca un valor dentro de una sección específica (dominio) del JSON.
    Los dominios válidos están definidos en DOMINIO_MAPEO.
    """
    dominio = dominio.lower().strip()
    if dominio not in DOMINIO_MAPEO:
        return {
            "error": f"Dominio '{dominio}' no reconocido. Opciones válidas: {list(DOMINIO_MAPEO.keys())}"
        }

    clave_dominio = DOMINIO_MAPEO[dominio]
    sub_json = json_data.get(clave_dominio)

    if sub_json is None:
        return {
            "warning": f"No se encontró la clave '{clave_dominio}' dentro del JSON. "
                       f"Verifica la estructura del legajo o dominio."
        }

    # Debug
    # print(f"[JSON_FALLBACK] Activado fallback para dominio '{dominio}' (clave raíz: '{clave_dominio}') con query: '{query}'")

    matches = _deep_search_dominio(sub_json, query)

    # Agrupar por hash del entry padre para evitar duplicados
    unique_results = {}
    for m in matches:
        key = str(m.get("full_entry"))
        if key not in unique_results or m["prioridad"] > unique_results[key]["prioridad"]:
            unique_results[key] = m

    sorted_results = sorted(unique_results.values(), key=lambda x: x["prioridad"], reverse=True)

    return {
        "dominio": dominio,
        "query": query,
        "matches_found": len(sorted_results),
        "results": sorted_results[:10],
    }
