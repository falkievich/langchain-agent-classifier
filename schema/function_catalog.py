"""
schema/function_catalog.py
──────────────────────────
Catálogo de funciones semánticas para el sistema de consultas.

ARQUITECTURA:
  - FUNCTION_CATALOG: Lo que ve el LLM (nombre, descripción, filtros posibles).
  - FUNCTION_PATHS:   Lo que NO ve el LLM (paths reales del JSON por función).

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
    # Dominio: personas_legajo (LISTA de personas involucradas en el expediente)
    # Son las PARTES PROCESALES del expediente: víctimas, imputados, actores,
    # demandados, querellantes, denunciantes, testigos.
    # NO son abogados ni funcionarios judiciales.
    # Cada persona tiene: datos personales, vinculos (rol procesal),
    # domicilios/contactos, caracteristicas sociales, relacionados (abogados embebidos),
    # y calificaciones legales.

    "get_personas": {
        "description": (
            "Obtiene las PARTES PROCESALES del expediente: víctimas, imputados, actores, "
            "demandados, querellantes, denunciantes, testigos. Devuelve datos personales "
            "(nombre, DNI, CUIL, fecha de nacimiento, género) y su rol procesal (vinculos). "
            "NO devuelve abogados ni funcionarios. "
            "Usar para: listar personas, buscar por nombre/DNI, filtrar por rol "
            "(victima, imputado, actor, demandado, querellante, testigo, denunciante), "
            "saber si alguien está detenido."
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
            "Obtiene los domicilios y contactos de las PARTES PROCESALES (personas, NO abogados). "
            "Los domicilios pueden ser FISICOS (dirección real: provincia, ciudad, calle) o "
            "ELECTRONICOS/DIGITALES (celular, teléfono, email). "
            "Usar para: dirección de una víctima, celular de un imputado, email de un testigo, "
            "filtrar personas que viven en una provincia/ciudad/municipio determinada. "
            "También usar cuando la consulta combina domicilio con otras condiciones "
            "(nombre + rol + ciudad + detenido) sobre la MISMA persona."
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
            "Obtiene los abogados/defensores EMBEBIDOS dentro de una persona del expediente "
            "(están en personas_legajo → relacionados). "
            "Usar para: 'abogado de la víctima', 'defensor del imputado', "
            "'quién defiende a [persona]'. "
            "IMPORTANTE: estos abogados están DENTRO de la persona en personas_legajo.relacionados, "
            "NO en abogados_legajo. "
            "Usar esta función cuando se pregunta por el abogado DE una persona específica "
            "(por su rol o nombre). Si se pregunta por abogados en general, usar get_abogados."
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
            "Obtiene los contactos/domicilios de los abogados EMBEBIDOS dentro de personas. "
            "Usar para: 'celular del abogado de la víctima', 'email del defensor del imputado'. "
            "NOTA: si se pide el contacto de un abogado general (no vinculado a una persona), "
            "usar get_domicilios_abogados en su lugar."
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
            "Obtiene el PERFIL SOCIAL de las partes procesales: ocupación, estado civil, "
            "nivel educativo, lugar de nacimiento, nacionalidad, nombre de padres, "
            "cantidad de hijos, si es menor de edad. "
            "Usar para: saber si alguien es menor, ocupación de un imputado, "
            "datos familiares de una víctima, nivel educativo. "
            "NO usar si la consulta involucra domicilios (usar get_domicilios_personas). "
            "NO confundir con datos del expediente (eso es cabecera_legajo)."
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
            "Obtiene las calificaciones legales asociadas a las personas (partes procesales) "
            "del expediente. Ejemplo: grado de participación, calificación penal específica. "
            "NO confundir con delitos del expediente (eso es get_delitos)."
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
    # Dominio: abogados_legajo (LISTA de abogados registrados en el expediente)
    # Son los PROFESIONALES JURÍDICOS: defensores (públicos, privados, oficiales),
    # apoderados, asesores de menores e incapaces, querellantes particulares.
    # Cada abogado tiene: datos personales, matrícula, tipo de vínculo jurídico,
    # domicilios/contactos propios, y la lista de personas que representan.
    # NO son partes procesales (víctimas/imputados/actores) → esos van en personas_legajo.
    # NO son funcionarios judiciales (fiscales/jueces) → esos van en funcionarios.

    "get_abogados": {
        "description": (
            "Obtiene los ABOGADOS registrados globalmente en el expediente. "
            "Son profesionales jurídicos: defensores (públicos, privados, oficiales), "
            "apoderados, asesores de menores. "
            "Incluye: nombre, DNI, matrícula, tipo de defensor/vínculo, y las personas que representan. "
            "Usar para: listar todos los abogados, buscar un abogado por nombre/matrícula, "
            "ver qué tipo de defensor es (público, privado, asesor de menores). "
            "NO confundir con personas del expediente (víctimas, imputados → get_personas). "
            "NO confundir con funcionarios judiciales (fiscal, juez → get_funcionarios)."
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
            "Obtiene contactos y domicilios de los ABOGADOS globales del expediente. "
            "Los domicilios pueden ser FISICOS (estudio jurídico, defensoría) o "
            "DIGITALES (celular, email). "
            "Usar para: celular/email de un defensor público, domicilio del abogado X, "
            "filtrar abogados por provincia/ciudad de su estudio."
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
            "Obtiene las personas REPRESENTADAS por cada abogado del expediente. "
            "Muestra qué persona (víctima, actor, demandado) defiende cada abogado. "
            "Incluye datos del representado, su rol procesal y domicilios. "
            "Usar para: 'a quién representa el defensor público', 'representados del abogado X', "
            "'clientes del defensor privado'."
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
    # Dominio: funcionarios (LISTA de funcionarios judiciales asignados al expediente)
    # Son los OPERADORES DE JUSTICIA: fiscales, jueces, secretarios, asesores, auxiliares.
    # NO son abogados (defensores) → esos van en abogados_legajo.
    # NO son partes procesales (víctimas/imputados) → esos van en personas_legajo.
    # Sus domicilios suelen ser solo un email institucional.

    "get_funcionarios": {
        "description": (
            "Obtiene los FUNCIONARIOS JUDICIALES asignados al expediente: fiscales, jueces, "
            "secretarios, auxiliares fiscales, asesores de menores (en su rol de funcionario). "
            "Incluye cargo, datos personales y email institucional. "
            "NO confundir con abogados/defensores (→ get_abogados). "
            "NO confundir con personas/partes procesales (→ get_personas). "
            "Usar para: quién es el fiscal, datos del juez, email del secretario."
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

    # ── EXPEDIENTE / CABECERA ────────────────────────────────
    # Dominio: cabecera_legajo (OBJETO escalar con metadatos administrativos del expediente)
    # Contiene toda la información ADMINISTRATIVA del legajo: CUIJ, número, año, tipo,
    # estado, carátulas, etapa procesal, prioridad, organismo, secretaría, ubicación,
    # materias, fechas de alta/modificación y usuarios responsables.
    # NO contiene personas, abogados, ni funcionarios.
    # NO contiene la descripción del hecho (eso es causa).
    # NO contiene datos técnicos del sistema (eso es _root → get_datos_sistema).

    "get_cabecera": {
        "description": (
            "Obtiene los DATOS ADMINISTRATIVOS del expediente: CUIJ, número, año, tipo, "
            "estado (Iniciado, En trámite, Archivado), carátulas, etapa procesal "
            "(Preparatoria, Juicio, Prueba, Ejecución, Sentencia, Investigación Penal Preparatoria), "
            "prioridad, organismo donde está radicado, secretaría, ubicación actual, "
            "materias, tipo de proceso, y usuarios responsables (alta, modificación). "
            "Usar para cualquier dato general/administrativo del expediente. "
            "IMPORTANTE: etapa_procesal_descripcion = fase/etapa del expediente. "
            "Usar este campo cuando la consulta mencione fase, etapa, instancia procesal. "
            "NO contiene nombres de personas, abogados ni funcionarios. "
            "NO contiene la descripción del hecho ni la fecha del hecho (eso es get_causa). "
            "NO contiene datos técnicos como servidor, base de datos o código de sistema (eso es get_datos_sistema)."
        ),
        "filters": {
            "etapa_procesal_descripcion":    "Fase/etapa del expediente: 'Preparatoria', 'Juicio', 'Prueba', 'Ejecución', 'Sentencia', etc.",
            "etapa_procesal_codigo":         "Código de la etapa procesal: 'ET_PRE', 'ET_JUI', 'ET_PRU', etc.",
            "estado_expediente_descripcion": "Estado del expediente: 'Iniciado', 'En trámite', 'Archivado', 'Paralizado', etc.",
            "estado_expediente_codigo":      "Código del estado: 'INIT', 'TRAM', 'ARCH', etc.",
            "tipo_expediente":               "Tipo de expediente: 'LJU', 'EXP', etc.",
            "prioridad":                     "Prioridad: 'MODERADO', 'ALTO', 'BAJO', etc.",
            "organismo_descripcion":         "Nombre del organismo donde está radicado",
            "ubicacion_actual_descripcion":  "Descripción de la ubicación actual del expediente",
        },
        "domain": "cabecera_legajo",
        "is_scalar": True,
    },

    "get_causa": {
        "description": (
            "Obtiene los datos del HECHO que origina el expediente: descripción narrativa "
            "del hecho, fecha del hecho, forma de inicio (denuncia, ampliación, de oficio) "
            "y carátulas. "
            "La descripción es un texto libre corto (ej: 'sustracción violenta de pertenencias'). "
            "NO contiene nombres de personas (esos van en personas_legajo). "
            "NO contiene delitos tipificados (esos van en materia_delitos → get_delitos). "
            "Usar para: qué pasó, cuándo ocurrió el hecho, cómo se inició la causa."
        ),
        "filters": {},
        "domain": "causa",
        "is_scalar": False,
    },

    "get_delitos": {
        "description": (
            "Obtiene los DELITOS y materias tipificados en el expediente "
            "(ej: 'ROBO AGRAVADO', 'LESIONES LEVES', 'AMENAZAS', 'APREMIO'). "
            "Cada delito tiene un código y una descripción. "
            "NO confundir con la descripción narrativa del hecho (eso es get_causa). "
            "NO contiene nombres de personas."
        ),
        "filters": {
            "codigo":      "Código del delito",
            "descripcion": "Descripción del delito",
        },
        "domain": "materia_delitos",
        "is_scalar": False,
    },

    "get_radicaciones": {
        "description": (
            "Obtiene el HISTORIAL DE RADICACIONES del expediente: cada movimiento entre "
            "organismos (fiscalía → juzgado → fiscalía), con fechas y motivos. "
            "Usar para: por dónde pasó el expediente, cuándo se movió, motivo de cada traslado."
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
            "Obtiene los ORGANISMOS Y DEPENDENCIAS que intervinieron en el expediente "
            "(fiscalías, juzgados, asesorías, oficinas judiciales). "
            "Incluye clase, jerarquía, rol (LEGAJO_OWNER, LEGAJO_VISTA, CONTROL_JUDICIAL) "
            "y períodos de actuación. "
            "NO confundir con radicaciones (que son los movimientos → get_radicaciones)."
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
        "description": (
            "Obtiene los CLASIFICADORES administrativos del expediente: etiquetas que "
            "categorizan el legajo (ej: 'CONSUMADO', 'PLURIPARTICIPACION', "
            "'VICTIMA MENOR DE EDAD', 'CON MEDIDA DE COERCION')."
        ),
        "filters": {
            "clasificador_codigo":      "Código del clasificador",
            "clasificador_descripcion": "Descripción del clasificador",
        },
        "domain": "clasificadores_legajo",
        "is_scalar": False,
    },

    "get_organismo_control": {
        "description": (
            "Obtiene el ORGANISMO DE CONTROL asociado al expediente "
            "(ej: el juzgado de garantías que supervisa). "
            "NO confundir con dependencias (→ get_dependencias) ni con "
            "el organismo de radicación actual (→ get_cabecera)."
        ),
        "filters": {},
        "domain": "organismo_control",
        "is_scalar": True,
    },

    "get_datos_sistema": {
        "description": (
            "Obtiene los datos TÉCNICOS/SISTEMA del legajo: clave interna, clave_causa, "
            "codigo_sistema (ej: 'THEMIS', 'iurixweb', 'iurixcl'), codigo_entidad, "
            "estado del procesamiento (PROCESADO, PENDIENTE), servidor, base de datos, "
            "fechas de auditoría y de creación. "
            "Usar cuando se pregunta de qué sistema proviene el legajo, "
            "datos internos de procesamiento, o si se mencionan palabras como "
            "'iurixweb', 'THEMIS', 'iurixcl', 'criminis' (son valores de codigo_sistema). "
            "NO confundir con datos administrativos del expediente (→ get_cabecera). "
            "NO confundir con estado del expediente (Iniciado/En trámite → get_cabecera)."
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
