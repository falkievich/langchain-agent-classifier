"""
extractors/registry.py
──────────────────────
Registro centralizado — REDIRIGE al nuevo catálogo de funciones semánticas.

En el enfoque anterior había 100+ funciones extractoras individuales.
Ahora hay ~15 funciones semánticas definidas en schema/function_catalog.py.

Este archivo se mantiene por compatibilidad pero delega todo al nuevo catálogo.
"""
from typing import Any, Dict, List

from schema.function_catalog import (
    FUNCTION_CATALOG,
    FUNCTION_PATHS,
    FUNCTION_KEYWORDS,
    get_function_names,
    get_function_domain,
    is_scalar_domain,
    get_function_paths,
)


# ═══════════════════════════════════════════════════════════════
#  Helpers de compatibilidad
# ═══════════════════════════════════════════════════════════════

TOOL_NAMES: List[str] = get_function_names()

# Mapeo nombre → metadata (para código que importe TOOL_BY_NAME)
TOOL_BY_NAME: Dict[str, Dict[str, Any]] = {
    name: FUNCTION_CATALOG[name] for name in FUNCTION_CATALOG
}
