from funcs.helpers_and_utility.fallback_resolvers import (
    resolver_por_codigo,
    resolver_por_nombre,
    resolver_por_descripcion,
)

def ejecutar_con_resolver(json_data, tool_func, arg=None, tipo=None):
    """
    Ejecuta una función específica. 
    Si no devuelve resultados, invoca el resolver correspondiente según 'tipo'.
    """

    result = tool_func(json_data, arg) if arg is not None else tool_func(json_data)

    # Detectamos vacío (dict vacío o todos los valores falsy)
    if not result or all(not v for v in result.values()):
        if tipo == "codigo":
            # Tipo = "codigo" → si no encuentra, prueba resolver_por_codigo
            return resolver_por_codigo(json_data, arg)
        elif tipo == "nombre":
            # Tipo = "nombre" → si no encuentra, prueba resolver_por_nombre
            return resolver_por_nombre(json_data, arg)
        elif tipo == "descripcion":
            # Tipo = "descripcion" → si no encuentra, prueba resolver_por_descripcion
            return resolver_por_descripcion(json_data, arg)

    return result
