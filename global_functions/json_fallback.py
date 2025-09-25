from typing import Any, Dict, List, Union

def _deep_search_with_parent(
    obj: Union[Dict, List],
    needle: str,
    path: str = "",
    parent: Any = None,
    parent_path: str = "",
) -> List[Dict[str, Any]]:
    """
    Recorre el JSON recursivamente buscando 'needle' en valores de texto o numéricos.
    Devuelve coincidencias con:
      - path exacto
      - value encontrado
      - full_entry (objeto completo de la lista o dict padre donde está el valor)
    """
    results = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if isinstance(v, (dict, list)):
                results.extend(
                    _deep_search_with_parent(
                        v,
                        needle,
                        new_path,
                        parent=obj,
                        parent_path=path or k,
                    )
                )
            else:
                try:
                    if needle.lower() in str(v).lower():
                        results.append({
                            "path": new_path,
                            "value": v,
                            "full_entry": parent if parent is not None else obj
                        })
                except Exception:
                    pass

    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            new_path = f"{path}[{idx}]"
            if isinstance(v, (dict, list)):
                results.extend(
                    _deep_search_with_parent(
                        v,
                        needle,
                        new_path,
                        parent=v,  # el item de la lista es el padre
                        parent_path=new_path,
                    )
                )
            else:
                try:
                    if needle.lower() in str(v).lower():
                        results.append({
                            "path": new_path,
                            "value": v,
                            "full_entry": parent if parent is not None else v
                        })
                except Exception:
                    pass

    return results


def buscar_en_json_global(json_data: Dict[str, Any], query: str) -> Dict[str, Any]:
    """
    Fallback interno: busca un string o número en TODO el JSON.
    Devuelve no solo el path y value, sino también la entrada completa del padre.
    """
    matches = _deep_search_with_parent(json_data, query)
    return {
        "query": query,
        "matches_found": len(matches),
        "results": matches[:50],  # limitar a 50 para no romper contexto
    }
