"""
schema/function_catalog.py
──────────────────────────
Catálogo de funciones semánticas para el sistema de consultas.

ARQUITECTURA:
  - FUNCTION_CATALOG: Lo que ve el LLM (nombre, descripción, filtros posibles).
  - FUNCTION_PATHS:   Lo que NO ve el LLM (paths reales del JSON por función).
  - FUNCTION_KEYWORDS: Palabras clave para el router determinístico (fallback).

El LLM elige función(es) + filtros opcionales.
El backend traduce eso a paths reales y ejecuta sobre el JSON.
"""
from typing import Any, Dict, List


# ═══════════════════════════════════════════════════════════════
#  CATÁLOGO SEMÁNTICO — visible al LLM
#  Cada función tiene:
#    - description: qué información devuelve y cuándo usarla
#    - filters:     campos por los que se puede filtrar + descripción
#    - domain:      sección principal del JSON (para el executor)
#    - is_scalar:   True si el dominio NO es una lista (ej: cabecera_legajo)
# ═══════════════════════════════════════════════════════════════

FUNCTION_CATALOG: Dict[str, Dict[str, Any]] = {

    # ── PERSONAS ──────────────────────────────────────────────

    "get_personas": {
        "description": (
            "Obtiene personas del expediente con sus datos personales y rol procesal. "
            "Usar para: listar personas, buscar por nombre/DNI, filtrar por rol "
            "(victima, imputado, actor, demandado, querellante)."
        ),
        "filters": {
            "vinculos.descripcion_vinculo": "Rol procesal: 'victima', 'imputado', 'actor', 'demandado'",
            "vinculos.codigo_vinculo":      "Código del rol: 'VIC', 'IMP', 'ACT', 'DEM'",
            "nombre":                       "Nombre de la persona",
            "apellido":                     "Apellido de la persona",
            "nombre_completo":              "Nombre completo de la persona",
            "numero_documento":             "DNI",
            "cuil":                         "CUIL",
            "genero":                       "Género: 'MASCULINO', 'FEMENINO'",
            "es_detenido":                  "Si está detenido: 'true' / 'false'",
        },
        "domain": "personas_legajo",
        "is_scalar": False,
    },

    "get_domicilios_personas": {
        "description": (
            "Obtiene los domicilios y contactos (celular, teléfono, email, domicilio físico) "
            "de las personas del expediente. "
            "Usar para: domicilios de víctimas, celulares de imputados, emails de personas, "
            "filtrar personas que viven en una provincia/ciudad/municipio determinada."
        ),
        "filters": {
            "vinculos.descripcion_vinculo":       "Rol procesal: 'victima', 'imputado', 'actor', 'demandado'",
            "vinculos.codigo_vinculo":            "Código del rol: 'VIC', 'IMP', 'ACT', 'DEM'",
            "domicilios.clase":                   "Tipo de domicilio: 'FISICO' (dirección) | 'ELECTRONICO' (contacto digital)",
            "domicilios.digital_clase":           "Tipo de contacto digital: 'Celular' | 'Teléfono' | 'Email'",
            "domicilios.digital_clase_codigo":    "Código contacto digital: 'CEL' | 'TEL' | 'EMAIL'",
            "domicilios.domicilio.provincia":     "Provincia del domicilio físico (ej: 'CORRIENTES', 'BUENOS AIRES')",
            "domicilios.domicilio.ciudad":        "Ciudad del domicilio físico (ej: 'CAPITAL', 'MERCEDES')",
            "domicilios.domicilio.municipio":     "Municipio del domicilio físico",
            "domicilios.domicilio.calle":         "Calle del domicilio físico (búsqueda parcial con op=contains)",
            "domicilios.domicilio.cpostal":       "Código postal del domicilio físico",
            "nombre":                             "Nombre de la persona",
            "nombre_completo":                    "Nombre completo",
            "numero_documento":                   "DNI",
        },
        "domain": "personas_legajo",
        "is_scalar": False,
    },

    "get_abogados_de_persona": {
        "description": (
            "Obtiene los abogados/defensores embebidos dentro de una persona del expediente. "
            "Usar para: 'abogado de la víctima', 'defensor del imputado', "
            "'quién defiende a [persona]'. "
            "IMPORTANTE: estos abogados están dentro de personas_legajo.relacionados, "
            "NO en abogados_legajo."
        ),
        "filters": {
            "vinculos.descripcion_vinculo":     "Rol de la persona defendida: 'victima', 'imputado'",
            "vinculos.codigo_vinculo":          "Código del rol: 'VIC', 'IMP'",
            "nombre":                           "Nombre de la persona defendida",
            "nombre_completo":                  "Nombre completo de la persona defendida",
            "numero_documento":                 "DNI de la persona defendida",
            "relacionados.vinculo_descripcion": "Tipo de defensor: 'defensor publico', 'defensor privado'",
            "relacionados.vinculo_codigo":      "Código tipo defensor",
        },
        "domain": "personas_legajo",
        "is_scalar": False,
    },

    "get_contactos_abogados_de_persona": {
        "description": (
            "Obtiene los contactos/domicilios de los abogados embebidos en personas. "
            "Usar para: 'celular del abogado de la víctima', 'email del defensor del imputado'."
        ),
        "filters": {
            "vinculos.descripcion_vinculo":            "Rol de la persona: 'victima', 'imputado'",
            "vinculos.codigo_vinculo":                 "Código del rol",
            "nombre":                                  "Nombre de la persona",
            "relacionados.vinculo_descripcion":        "Tipo de defensor",
            "relacionados.domicilios.digital_clase":   "Tipo contacto: 'Celular', 'Teléfono', 'Email'",
            "relacionados.domicilios.digital_clase_codigo": "Código contacto: 'CEL', 'TEL', 'EMAIL'",
            "relacionados.domicilios.clase":           "Clase: 'FISICO', 'ELECTRONICO'",
        },
        "domain": "personas_legajo",
        "is_scalar": False,
    },

    "get_caracteristicas_personas": {
        "description": (
            "Obtiene características sociales de las personas: ocupación, estado civil, "
            "nivel educativo, lugar de nacimiento, nombre de padres, cantidad de hijos. "
            "Usar para: perfil social de imputados, si es menor, datos familiares."
        ),
        "filters": {
            "vinculos.descripcion_vinculo":     "Rol: 'victima', 'imputado'",
            "vinculos.codigo_vinculo":          "Código del rol",
            "nombre":                           "Nombre de la persona",
            "nombre_completo":                  "Nombre completo",
            "numero_documento":                 "DNI",
            "caracteristicas.es_menor":         "'true' / 'false'",
            "caracteristicas.ocupacion":        "Ocupación",
            "caracteristicas.estado_civil":     "Estado civil",
            "caracteristicas.lugar_nacimiento": "Lugar de nacimiento",
            "es_detenido":                      "Si está detenido: 'true' / 'false'",
        },
        "domain": "personas_legajo",
        "is_scalar": False,
    },

    "get_calificaciones_legales_personas": {
        "description": (
            "Obtiene las calificaciones legales asociadas a las personas del expediente."
        ),
        "filters": {
            "vinculos.descripcion_vinculo": "Rol: 'victima', 'imputado'",
            "vinculos.codigo_vinculo":      "Código del rol",
            "nombre":                       "Nombre de la persona",
            "nombre_completo":              "Nombre completo",
            "numero_documento":             "DNI",
        },
        "domain": "personas_legajo",
        "is_scalar": False,
    },

    # ── ABOGADOS (registro global) ─────────────────────────────

    "get_abogados": {
        "description": (
            "Obtiene los abogados registrados globalmente en el expediente "
            "(no los embebidos en personas). Incluye matrícula, tipo de defensor "
            "y las personas que representan. "
            "Usar para: listar defensores, buscar por matrícula, ver representados."
        ),
        "filters": {
            "nombre":              "Nombre del abogado",
            "apellido":            "Apellido del abogado",
            "nombre_completo":     "Nombre completo del abogado",
            "numero_documento":    "DNI del abogado",
            "cuil":                "CUIL del abogado",
            "matricula":           "Matrícula",
            "vinculo_descripcion": "Tipo: 'defensor publico', 'defensor privado', 'asesor de menores e incapaces'",
            "vinculo_codigo":      "Código del tipo de defensor",
        },
        "domain": "abogados_legajo",
        "is_scalar": False,
    },

    "get_domicilios_abogados": {
        "description": (
            "Obtiene contactos y domicilios de los abogados globales. "
            "Usar para: celular/email del defensor público, domicilio del abogado X, "
            "filtrar abogados que tienen domicilio en una provincia/ciudad determinada."
        ),
        "filters": {
            "nombre":                             "Nombre del abogado",
            "nombre_completo":                    "Nombre completo del abogado",
            "matricula":                          "Matrícula",
            "vinculo_descripcion":                "Tipo: 'defensor publico', 'defensor privado'",
            "vinculo_codigo":                     "Código del tipo",
            "domicilios.clase":                   "Tipo de domicilio: 'FISICO' (dirección) | 'ELECTRONICO' (contacto digital)",
            "domicilios.digital_clase":           "Tipo de contacto digital: 'Celular' | 'Teléfono' | 'Email'",
            "domicilios.digital_clase_codigo":    "Código contacto digital: 'CEL' | 'TEL' | 'EMAIL'",
            "domicilios.domicilio.provincia":     "Provincia del domicilio físico (ej: 'CORRIENTES', 'BUENOS AIRES')",
            "domicilios.domicilio.ciudad":        "Ciudad del domicilio físico (ej: 'CAPITAL', 'MERCEDES')",
            "domicilios.domicilio.municipio":     "Municipio del domicilio físico",
            "domicilios.domicilio.calle":         "Calle del domicilio físico (búsqueda parcial con op=contains)",
            "domicilios.domicilio.cpostal":       "Código postal del domicilio físico",
        },
        "domain": "abogados_legajo",
        "is_scalar": False,
    },

    "get_representados_abogados": {
        "description": (
            "Obtiene las personas representadas por cada abogado del expediente. "
            "Incluye datos del representado, su rol procesal y domicilios. "
            "Usar para: 'a quién representa el defensor público', 'representados del abogado X'."
        ),
        "filters": {
            "nombre":                              "Nombre del abogado",
            "nombre_completo":                     "Nombre completo del abogado",
            "matricula":                           "Matrícula",
            "vinculo_descripcion":                 "Tipo: 'defensor publico', 'defensor privado'",
            "representados.vinculo_descripcion":   "Rol del representado: 'ACTOR', 'DEMANDADO'",
            "representados.nombre_completo":       "Nombre del representado",
            "representados.numero_documento":      "DNI del representado",
        },
        "domain": "abogados_legajo",
        "is_scalar": False,
    },

    # ── FUNCIONARIOS ──────────────────────────────────────────

    "get_funcionarios": {
        "description": (
            "Obtiene los funcionarios judiciales del expediente: fiscales, jueces, "
            "secretarios. Incluye cargo, datos personales y email."
        ),
        "filters": {
            "nombre_completo":  "Nombre del funcionario",
            "numero_documento": "DNI",
            "cuil":             "CUIL",
            "cargo":            "'fiscal', 'juez', 'secretario', etc.",
        },
        "domain": "funcionarios",
        "is_scalar": False,
    },

    # ── EXPEDIENTE ────────────────────────────────────────────

    "get_cabecera": {
        "description": (
            "Obtiene los datos generales del expediente: CUIJ, número, año, tipo, "
            "estado, carátulas, fechas, organismo, etapa procesal, secretaría, "
            "ubicación actual, materias y usuarios responsables. "
            "Usar para cualquier dato general del expediente."
        ),
        "filters": {},
        "domain": "cabecera_legajo",
        "is_scalar": True,
    },

    "get_causa": {
        "description": (
            "Obtiene los datos del hecho que origina el expediente: descripción, "
            "fecha del hecho, forma de inicio y carátulas de la causa."
        ),
        "filters": {},
        "domain": "causa",
        "is_scalar": False,
    },

    "get_delitos": {
        "description": "Obtiene los delitos y materias asociados al expediente.",
        "filters": {
            "codigo":      "Código del delito",
            "descripcion": "Descripción del delito",
        },
        "domain": "materia_delitos",
        "is_scalar": False,
    },

    "get_radicaciones": {
        "description": (
            "Obtiene el historial de radicaciones del expediente: "
            "movimientos entre organismos, motivos y fechas."
        ),
        "filters": {
            "organismo_actual_codigo":      "Código del organismo",
            "organismo_actual_descripcion": "Nombre del organismo",
            "motivo_actual_descripcion":    "Descripción del motivo",
            "fecha_desde":                  "Fecha inicio (YYYY-MM-DD)",
            "fecha_hasta":                  "Fecha fin (YYYY-MM-DD)",
        },
        "domain": "radicaciones",
        "is_scalar": False,
    },

    "get_dependencias": {
        "description": (
            "Obtiene los organismos y dependencias que intervinieron en el expediente. "
            "Incluye clase, jerarquía, rol y períodos de actuación."
        ),
        "filters": {
            "organismo_codigo":       "Código del organismo",
            "organismo_descripcion":  "Nombre del organismo",
            "dependencia_descripcion":"Nombre de la dependencia",
            "clase_descripcion":      "Clase de dependencia",
            "rol":                    "Rol en el expediente",
            "activo":                 "'true' / 'false'",
        },
        "domain": "dependencias_vistas",
        "is_scalar": False,
    },

    "get_clasificadores": {
        "description": "Obtiene los clasificadores administrativos del expediente.",
        "filters": {
            "clasificador_codigo":      "Código del clasificador",
            "clasificador_descripcion": "Descripción del clasificador",
        },
        "domain": "clasificadores_legajo",
        "is_scalar": False,
    },

    "get_organismo_control": {
        "description": "Obtiene el organismo de control asociado al expediente.",
        "filters": {},
        "domain": "organismo_control",
        "is_scalar": True,
    },

    "get_datos_sistema": {
        "description": (
            "Obtiene los datos técnicos/sistema del legajo: clave, clave_causa, "
            "código de sistema, estado del procesamiento, servidor, base de datos, fechas de auditoría."
        ),
        "filters": {},
        "domain": "_root",
        "is_scalar": True,
    },
}


# ═══════════════════════════════════════════════════════════════
#  MAPEO DE PATHS REALES — NO visible al LLM (backend puro)
#  Cada función tiene la lista de paths que debe extraer del JSON.
#  Los paths son relativos al dominio (excepto _root).
# ═══════════════════════════════════════════════════════════════

FUNCTION_PATHS: Dict[str, List[str]] = {

    # ── PERSONAS ──────────────────────────────────────────────

    "get_personas": [
        "persona_id",
        "nombre", "apellido", "nombre_completo",
        "tipo_documento", "numero_documento", "cuil",
        "fecha_nacimiento", "genero", "es_detenido",
        "fecha_desde", "fecha_hasta",
        # vinculos (sub-lista)
        "vinculos",
    ],

    "get_domicilios_personas": [
        "persona_id",
        "nombre_completo",
        "vinculos",
        # domicilios (sub-lista completa)
        "domicilios",
    ],

    "get_abogados_de_persona": [
        "persona_id",
        "nombre_completo",
        "vinculos",
        # relacionados (sub-lista completa)
        "relacionados",
    ],

    "get_contactos_abogados_de_persona": [
        "persona_id",
        "nombre_completo",
        "vinculos",
        # relacionados con sus domicilios
        "relacionados",
    ],

    "get_caracteristicas_personas": [
        "persona_id",
        "nombre_completo",
        "tipo_documento", "numero_documento", "cuil",
        "vinculos",
        "es_detenido",
        # caracteristicas (sub-lista completa)
        "caracteristicas",
    ],

    "get_calificaciones_legales_personas": [
        "persona_id",
        "nombre_completo",
        "vinculos",
        "calificaciones_legales",
    ],

    # ── ABOGADOS (registro global) ─────────────────────────────

    "get_abogados": [
        "abogado_id", "abogado_persona_id",
        "nombre", "apellido", "nombre_completo",
        "tipo_documento", "numero_documento", "cuil",
        "matricula",
        "vinculo_codigo", "vinculo_descripcion",
        "fecha_nacimiento", "fecha_desde", "fecha_hasta",
        # representados resumido
        "representados",
    ],

    "get_domicilios_abogados": [
        "abogado_id",
        "nombre_completo",
        "matricula",
        "vinculo_codigo", "vinculo_descripcion",
        # domicilios (sub-lista completa)
        "domicilios",
    ],

    "get_representados_abogados": [
        "abogado_id",
        "nombre_completo",
        "matricula",
        "vinculo_codigo", "vinculo_descripcion",
        # representados (sub-lista completa con domicilios y vinculos)
        "representados",
    ],

    # ── FUNCIONARIOS ──────────────────────────────────────────

    "get_funcionarios": [
        "funcionario_id",
        "nombre_completo",
        "tipo_documento", "numero_documento", "cuil",
        "cargo",
        "fecha_desde", "fecha_hasta",
        "observaciones",
        "domicilios",
    ],

    # ── EXPEDIENTE ────────────────────────────────────────────

    "get_cabecera": [
        "clave", "ide", "legajo_id", "orden_sufijo",
        "organismo_codigo", "organismo_descripcion",
        "tipo_expediente", "numero_expediente", "anio_expediente",
        "estado_expediente_codigo", "estado_expediente_descripcion",
        "fecha_registro", "fecha_inicio", "fecha_modificacion",
        "nivel_acceso",
        "caratula_publica", "caratula_privada",
        "usuario_alta", "usuario_baja", "usuario_modificacion",
        "dependencia_radicacion_codigo", "dependencia_radicacion_descripcion",
        "tipo_proceso",
        "etapa_procesal_codigo", "etapa_procesal_descripcion",
        "prioridad", "cuij",
        "materias",
        "ubicacion_actual_codigo", "ubicacion_actual_descripcion",
        "secretaria_codigo", "secretaria_descripcion",
    ],

    "get_causa": [
        "causa_id",
        "descripcion", "fecha_hecho", "forma_inicio",
        "dependencia_id",
        "nivel_acceso_id", "nivel_acceso_descripcion",
        "caratula_publica", "caratula_privada",
    ],

    "get_delitos": [
        "materia_id", "codigo", "descripcion", "grado_id", "orden",
    ],

    "get_radicaciones": [
        "radicacion_id", "expediente_id",
        "organismo_actual_codigo", "organismo_actual_descripcion",
        "fecha_desde", "fecha_hasta",
        "motivo_actual_codigo", "motivo_actual_descripcion",
        "observaciones",
    ],

    "get_dependencias": [
        "organismo_codigo", "organismo_descripcion",
        "dependencia_id", "dependencia_codigo", "dependencia_descripcion",
        "clase_codigo", "clase_descripcion",
        "fecha_desde", "fecha_hasta",
        "activo", "dependencia_jerarquia", "rol",
        "tipos",
    ],

    "get_clasificadores": [
        "clasificador_id",
        "clasificador_codigo", "clasificador_descripcion",
        "clasificador_clase_id", "clasificador_clase_codigo",
    ],

    "get_organismo_control": [
        "organismo_codigo", "organismo_descripcion",
    ],

    "get_datos_sistema": [
        "fecha_creacion", "proceso_id",
        "servidor", "base_datos",
        "estado", "clave", "clave_causa",
        "codigo_sistema", "codigo_entidad",
        "motivo_col", "motivo_act",
        "seguridad",
        "fecha_radicacion", "fecha_control",
        "fecha_auditoria", "fecha_auditoria_tmz",
    ],
}


# ═══════════════════════════════════════════════════════════════
#  KEYWORDS PARA ROUTER DETERMINÍSTICO (fallback sin LLM)
# ═══════════════════════════════════════════════════════════════

FUNCTION_KEYWORDS: Dict[str, List[str]] = {

    "get_personas": [
        "persona", "personas", "imputado", "victima", "actor", "demandado",
        "querellante", "denunciante", "testigo", "detenido",
        "listar personas", "todas las personas", "quienes participan",
        "involucrados", "nombre persona", "dni persona",
    ],

    "get_domicilios_personas": [
        "domicilio persona", "domicilios personas", "direccion persona",
        "celular persona", "telefono persona", "email persona",
        "contacto persona", "celular victima", "celular imputado",
        "telefono victima", "domicilio victima", "domicilio imputado",
        "vive en", "quien vive en", "personas en corrientes", "personas en buenos aires",
        "provincia persona", "ciudad persona", "municipio persona",
        "donde vive", "domicilio en", "direccion en",
    ],

    "get_abogados_de_persona": [
        "abogado de la victima", "abogado del imputado",
        "defensor del imputado", "defensor de la victima",
        "quien defiende", "quien representa a la persona",
        "abogado de persona", "defensor de persona",
    ],

    "get_contactos_abogados_de_persona": [
        "celular abogado victima", "telefono defensor imputado",
        "email abogado de persona", "contacto defensor de",
        "celular del abogado de la victima", "celular del defensor del imputado",
    ],

    "get_caracteristicas_personas": [
        "caracteristicas", "caracteristica persona", "perfil social",
        "ocupacion", "estado civil", "nivel educativo",
        "lugar nacimiento", "nombre madre", "nombre padre",
        "menor", "es menor", "datos familiares",
    ],

    "get_calificaciones_legales_personas": [
        "calificaciones legales", "calificacion legal",
        "calificacion persona",
    ],

    "get_abogados": [
        "abogado", "abogados", "defensor", "defensores",
        "todos los abogados", "listar abogados",
        "matricula", "defensor publico", "defensor privado",
    ],

    "get_domicilios_abogados": [
        "domicilio abogado", "domicilios abogados",
        "celular abogado", "telefono abogado", "email abogado",
        "contacto abogado", "direccion abogado",
        "celular defensor", "telefono defensor",
        "abogado en corrientes", "abogado en buenos aires",
        "provincia abogado", "ciudad abogado", "donde vive el abogado",
        "domicilio del defensor", "donde vive el defensor",
    ],

    "get_representados_abogados": [
        "representado", "representados", "a quien representa",
        "cliente abogado", "clientes",
    ],

    "get_funcionarios": [
        "funcionario", "funcionarios", "fiscal", "juez", "secretario",
        "todos los funcionarios", "email funcionario",
        "domicilio funcionario", "cargo",
    ],

    "get_cabecera": [
        "expediente", "cabecera", "legajo", "cuij", "caratula",
        "informacion general", "datos generales", "estado expediente",
        "tipo expediente", "numero expediente", "año expediente",
        "etapa procesal", "prioridad", "organismo", "secretaria",
        "ubicacion actual", "tipo proceso", "fecha inicio", "fecha modificacion",
    ],

    "get_causa": [
        "causa", "hecho", "fecha hecho", "forma inicio",
        "de que se trata", "que paso", "caratula causa",
    ],

    "get_delitos": [
        "delito", "delitos", "materia", "materias",
        "codigo delito", "que delito",
    ],

    "get_radicaciones": [
        "radicacion", "radicaciones", "movimiento", "movimientos",
        "motivo radicacion", "por donde paso",
    ],

    "get_dependencias": [
        "dependencia", "dependencias", "organismos que intervinieron",
        "por que dependencias paso", "instituciones",
    ],

    "get_clasificadores": [
        "clasificador", "clasificadores", "clasificacion",
        "categorias", "tipo legajo",
    ],

    "get_organismo_control": [
        "organismo control", "quien controla",
        "organismo de control",
    ],

    "get_datos_sistema": [
        "datos sistema", "sistema", "codigo sistema", "codigo entidad",
        "estado legajo", "procesado", "servidor", "base datos",
        "clave causa", "seguridad", "auditoria",
    ],
}


# ═══════════════════════════════════════════════════════════════
#  PATHS DISPONIBLES POR FUNCIÓN — visible al LLM
#
#  El LLM elige un subconjunto de estos paths según la consulta
#  y los incluye en output_paths del step.
#
#  CONVENCIÓN (paths relativos al dominio de la función):
#    - Campos de primer nivel: "nombre_completo", "matricula"
#    - Sub-campos de una lista: "domicilios.domicilio.provincia"
#    - Sub-campos de un objeto anidado: "caracteristicas.ocupacion"
#    - ["*"] significa "devolver todo" (funciones escalares o consultas amplias)
#
#  REGLA: persona_id / abogado_id / funcionario_id siempre se
#  incluyen automáticamente en el executor (no hace falta pedirlos).
# ═══════════════════════════════════════════════════════════════

FUNCTION_AVAILABLE_PATHS: Dict[str, List[str]] = {

    "get_personas": [
        "nombre_completo",
        "numero_documento",
        "cuil",
        "genero",
        "fecha_nacimiento",
        "es_detenido",
        "vinculos",
    ],

    "get_domicilios_personas": [
        "nombre_completo",
        "vinculos",
        "domicilios.tipo",
        "domicilios.clase",
        "domicilios.digital_clase",
        "domicilios.descripcion",
        "domicilios.domicilio.pais",
        "domicilios.domicilio.provincia",
        "domicilios.domicilio.ciudad",
        "domicilios.domicilio.municipio",
        "domicilios.domicilio.calle",
        "domicilios.domicilio.numero",
        "domicilios.domicilio.piso",
        "domicilios.domicilio.cpostal",
        "domicilios.domicilio.barrio",
    ],

    "get_abogados_de_persona": [
        "nombre_completo",
        "vinculos",
        "relacionados.nombre_completo",
        "relacionados.numero_documento",
        "relacionados.cuil",
        "relacionados.matricula",
        "relacionados.vinculo_descripcion",
    ],

    "get_contactos_abogados_de_persona": [
        "nombre_completo",
        "vinculos",
        "relacionados.nombre_completo",
        "relacionados.vinculo_descripcion",
        "relacionados.domicilios.digital_clase",
        "relacionados.domicilios.descripcion",
    ],

    "get_caracteristicas_personas": [
        "nombre_completo",
        "vinculos",
        "es_detenido",
        "caracteristicas.ocupacion",
        "caracteristicas.estado_civil",
        "caracteristicas.lugar_nacimiento",
        "caracteristicas.nacionalidad",
        "caracteristicas.es_menor",
        "caracteristicas.nombre_madre",
        "caracteristicas.nombre_padre",
        "caracteristicas.cantidad_hijos",
        "caracteristicas.nivel_educativo",
    ],

    "get_calificaciones_legales_personas": [
        "nombre_completo",
        "vinculos",
        "calificaciones_legales",
    ],

    "get_abogados": [
        "nombre_completo",
        "numero_documento",
        "cuil",
        "matricula",
        "vinculo_descripcion",
        "vinculo_codigo",
        "representados",
    ],

    "get_domicilios_abogados": [
        "nombre_completo",
        "matricula",
        "vinculo_descripcion",
        "domicilios.tipo",
        "domicilios.clase",
        "domicilios.digital_clase",
        "domicilios.descripcion",
        "domicilios.domicilio.pais",
        "domicilios.domicilio.provincia",
        "domicilios.domicilio.ciudad",
        "domicilios.domicilio.municipio",
        "domicilios.domicilio.calle",
        "domicilios.domicilio.numero",
        "domicilios.domicilio.cpostal",
    ],

    "get_representados_abogados": [
        "nombre_completo",
        "matricula",
        "vinculo_descripcion",
        "representados.nombre_completo",
        "representados.numero_documento",
        "representados.vinculo_descripcion",
        "representados.domicilios",
    ],

    "get_funcionarios": [
        "nombre_completo",
        "numero_documento",
        "cuil",
        "cargo",
        "domicilios",
    ],

    # Funciones escalares: paths concretos (el LLM elige un subconjunto)
    "get_cabecera": [
        "cuij",
        "numero_expediente", "anio_expediente", "tipo_expediente",
        "estado_expediente_codigo", "estado_expediente_descripcion",
        "fecha_registro", "fecha_inicio", "fecha_modificacion",
        "caratula_publica", "caratula_privada",
        "organismo_codigo", "organismo_descripcion",
        "dependencia_radicacion_codigo", "dependencia_radicacion_descripcion",
        "etapa_procesal_codigo", "etapa_procesal_descripcion",
        "ubicacion_actual_codigo", "ubicacion_actual_descripcion",
        "secretaria_codigo", "secretaria_descripcion",
        "tipo_proceso", "prioridad", "nivel_acceso",
        "materias",
        "usuario_alta", "usuario_baja", "usuario_modificacion",
    ],

    "get_causa": [
        "causa_id",
        "descripcion", "fecha_hecho", "forma_inicio",
        "nivel_acceso_descripcion",
        "caratula_publica", "caratula_privada",
    ],

    "get_delitos": [
        "codigo", "descripcion", "grado_id", "orden",
    ],

    "get_radicaciones": [
        "organismo_actual_codigo", "organismo_actual_descripcion",
        "fecha_desde", "fecha_hasta",
        "motivo_actual_codigo", "motivo_actual_descripcion",
        "observaciones",
    ],

    "get_dependencias": [
        "organismo_codigo", "organismo_descripcion",
        "dependencia_codigo", "dependencia_descripcion",
        "clase_codigo", "clase_descripcion",
        "fecha_desde", "fecha_hasta",
        "activo", "rol",
    ],

    "get_clasificadores": [
        "clasificador_codigo", "clasificador_descripcion",
        "clasificador_clase_codigo",
    ],

    "get_organismo_control": [
        "organismo_codigo", "organismo_descripcion",
    ],

    "get_datos_sistema": [
        "estado", "clave", "clave_causa",
        "codigo_sistema", "codigo_entidad",
        "servidor", "base_datos",
        "fecha_creacion", "fecha_radicacion",
        "fecha_auditoria", "fecha_auditoria_tmz",
    ],
}


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def get_function_names() -> List[str]:
    """Devuelve la lista de nombres de funciones disponibles."""
    return list(FUNCTION_CATALOG.keys())


def get_function_domain(function_name: str) -> str:
    """Devuelve el dominio del JSON al que pertenece una función."""
    meta = FUNCTION_CATALOG.get(function_name, {})
    return meta.get("domain", "")


def is_scalar_domain(function_name: str) -> bool:
    """Devuelve True si el dominio de la función es escalar (no es lista)."""
    meta = FUNCTION_CATALOG.get(function_name, {})
    return meta.get("is_scalar", False)


def get_function_paths(function_name: str) -> List[str]:
    """Devuelve los paths reales que debe extraer una función."""
    return FUNCTION_PATHS.get(function_name, [])


def get_available_paths(function_name: str) -> List[str]:
    """Devuelve los paths que el LLM puede solicitar para una función."""
    return FUNCTION_AVAILABLE_PATHS.get(function_name, ["*"])
