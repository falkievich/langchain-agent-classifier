"""
tools/llm_planner.py
────────────────────
Planner LLM: genera un plan de funciones semánticas.

El LLM recibe:
  - La consulta del usuario
  - El catálogo de funciones semánticas (nombre + descripción + filtros + paths disponibles)

Y devuelve un plan JSON con steps:
  {
    "steps": [
      {
        "step_id": 1,
        "function": "get_personas",
        "filters": [{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}],
        "output_paths": ["nombre_completo", "vinculos", "numero_documento"]
      }
    ]
  }

IMPORTANTE: El LLM SOLO genera el plan. No ejecuta nada. La ejecución es determinística.
"""
import json
import re
from typing import Any, Dict, List, Optional

from schema.call_and_plan_schema import Plan, Step, StepFilter
from schema.function_catalog import FUNCTION_CATALOG, FUNCTION_AVAILABLE_PATHS


# ═══════════════════════════════════════════════════════════════
#  Catálogo de funciones para el prompt (se genera dinámicamente)
# ═══════════════════════════════════════════════════════════════

def _build_function_catalog() -> str:
    """Genera el catálogo de funciones disponibles para incluir en el system prompt."""
    lines = []
    for fname, meta in FUNCTION_CATALOG.items():
        desc = meta["description"]
        filters = meta.get("filters", {})
        available_paths = FUNCTION_AVAILABLE_PATHS.get(fname, ["*"])

        filters_str = ""
        if filters:
            filter_items = ", ".join(f"{k} ({v})" for k, v in filters.items())
            filters_str = f"\n    Filtros: {filter_items}"

        paths_str = ""
        if available_paths != ["*"]:
            paths_str = f"\n    Paths disponibles: {available_paths}"
        else:
            paths_str = "\n    Paths disponibles: [*] (devuelve todo)"

        lines.append(f"• {fname}\n    {desc}{filters_str}{paths_str}")
    return "\n\n".join(lines)


_FUNCTION_CATALOG_TEXT = _build_function_catalog()


# ═══════════════════════════════════════════════════════════════
#  System prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = f"""Eres un planificador de consultas sobre expedientes judiciales argentinos.
Devuelve SOLO JSON válido. Sin texto adicional, sin markdown, sin backticks.

══════════════════════════════════════════════════════════
 MAPA DE DOMINIOS — QUÉ ES CADA COSA Y DÓNDE BUSCARLA
══════════════════════════════════════════════════════════

El legajo judicial tiene dominios separados. Cada dominio guarda un tipo de información DIFERENTE.
Antes de armar el plan, SIEMPRE identificá a cuál dominio pertenece lo que pide el usuario.

1. personas_legajo (LISTA) — PARTES PROCESALES
   Quiénes: víctimas, imputados, actores, demandados, querellantes, denunciantes, testigos.
   Qué tiene: nombre, DNI, CUIL, fecha de nacimiento, género, si está detenido,
              vinculos (rol procesal), domicilios (dirección física, celular, email),
              caracteristicas (ocupación, estado civil, es_menor, lugar nacimiento, padres),
              relacionados (abogados embebidos dentro de la persona),
              calificaciones_legales.
   NO son abogados. NO son funcionarios. NO son datos del expediente.

2. abogados_legajo (LISTA) — PROFESIONALES JURÍDICOS
   Quiénes: defensores públicos, defensores privados, defensores oficiales,
            apoderados, asesores de menores e incapaces, querellantes particulares.
   Qué tiene: nombre, DNI, matrícula, tipo de vínculo (vinculo_descripcion),
              domicilios/contactos propios, representados (las personas que defienden).
   NO son víctimas/imputados. NO son fiscales/jueces.
   Diferencia con "relacionados" de personas: abogados_legajo es el registro GLOBAL,
   personas_legajo.relacionados es el abogado EMBEBIDO dentro de una persona específica.

3. funcionarios (LISTA) — OPERADORES DE JUSTICIA
   Quiénes: fiscales, jueces, secretarios, auxiliares fiscales, asesores de menores (en su rol judicial).
   Qué tiene: nombre, DNI, CUIL, cargo, email institucional.
   NO son abogados/defensores. NO son partes procesales.

4. cabecera_legajo (OBJETO escalar) — DATOS ADMINISTRATIVOS DEL EXPEDIENTE
   Qué tiene: CUIJ, número, año, tipo de expediente, estado (Iniciado, En trámite, Archivado),
              carátulas, etapa procesal (Preparatoria, Juicio, Prueba, Ejecución, Sentencia,
              Investigación Penal Preparatoria), prioridad, organismo, secretaría,
              ubicación actual, materias, tipo de proceso, usuarios responsables.
   NO contiene personas, abogados, ni funcionarios.
   NO contiene la descripción del hecho (eso es causa).
   NO contiene datos técnicos del sistema (eso es _root).

5. causa (LISTA o OBJETO) — EL HECHO
   Qué tiene: descripción narrativa del hecho (texto corto), fecha del hecho,
              forma de inicio (denuncia, ampliación, de oficio), carátulas.
   NO contiene nombres de personas. NO contiene delitos tipificados.

6. materia_delitos (LISTA) — DELITOS TIPIFICADOS
   Qué tiene: código y descripción del delito (ej: "ROBO AGRAVADO", "LESIONES LEVES").
   NO confundir con la descripción narrativa del hecho (eso es causa).

7. radicaciones (LISTA) — HISTORIAL DE MOVIMIENTOS
   Qué tiene: de qué organismo a cuál pasó, cuándo, por qué motivo.

8. dependencias_vistas (LISTA) — ORGANISMOS INTERVINIENTES
   Qué tiene: fiscalías, juzgados, asesorías que intervinieron, con rol y período.

9. clasificadores_legajo (LISTA) — ETIQUETAS ADMINISTRATIVAS
   Qué tiene: clasificadores como "CONSUMADO", "PLURIPARTICIPACION", "VICTIMA MENOR DE EDAD".

10. organismo_control (OBJETO escalar) — ORGANISMO DE CONTROL
    Qué tiene: el juzgado/organismo que supervisa el expediente.

11. _root (OBJETO escalar) — DATOS TÉCNICOS/SISTEMA
    Qué tiene: clave interna, clave_causa, codigo_sistema, servidor, base_datos,
               estado del procesamiento (PROCESADO/PENDIENTE), fechas de auditoría.
    IMPORTANTE: "iurixweb", "THEMIS", "iurixcl", "criminis" son valores del campo
    codigo_sistema. Si el usuario menciona alguna de estas palabras, está preguntando
    por datos del sistema → usar get_datos_sistema.

══ REGLA CLAVE: ¿QUIÉN ES QUIÉN? ══
  • "víctima", "imputado", "actor", "demandado", "querellante", "denunciante", "testigo"
    → SIEMPRE en personas_legajo (funciones get_personas, get_domicilios_personas, etc.)
  • "abogado", "defensor", "apoderado", "asesor de menores"
    → SIEMPRE en abogados_legajo (funciones get_abogados, get_domicilios_abogados, etc.)
    → EXCEPCIÓN: "abogado DE la víctima" / "defensor DEL imputado"
      → usar get_abogados_de_persona (busca en personas_legajo.relacionados)
  • "fiscal", "juez", "secretario"
    → SIEMPRE en funcionarios (función get_funcionarios)
  • "CUIJ", "estado del expediente", "etapa procesal", "carátula", "prioridad", "organismo"
    → SIEMPRE en cabecera_legajo (función get_cabecera)
  • "qué pasó", "descripción del hecho", "fecha del hecho", "cómo se inició"
    → SIEMPRE en causa (función get_causa)
  • "qué delito", "tipificación"
    → SIEMPRE en materia_delitos (función get_delitos)
  • "de qué sistema es", "iurixweb", "THEMIS", "iurixcl", "criminis", "servidor", "base de datos"
    → SIEMPRE en _root (función get_datos_sistema)

══════════════════════════════════════════════════════════
 FUNCIONES DISPONIBLES
══════════════════════════════════════════════════════════
{_FUNCTION_CATALOG_TEXT}

══════════════════════════════════════════════════════════
 REGLAS GENERALES
══════════════════════════════════════════════════════════
1. Elige la(s) función(es) que mejor responden la consulta.
2. Agrega filtros solo si la consulta especifica una condición (rol, nombre, tipo de contacto).
3. Para preguntas simples: 1 función, 0-1 filtros.
4. Para preguntas compuestas que involucran múltiples entidades independientes: múltiples funciones en paralelo (sin depends_on).
5. No encadenes steps si la respuesta está en una sola función.
6. depends_on SOLO cuando necesitas el resultado del step anterior para filtrar el siguiente.
7. Los values en filters son siempre strings.
8. Operadores de comparación: eq (igual exacto) | contains (contiene, case-insensitive) | gte (>=) | lte (<=) | neq (distinto)

OPERADORES LÓGICOS (campos opcionales del step):
• "filter_op": "AND" (default) | "OR"
    AND → todos los filtros del step deben cumplirse (default, no hace falta declararlo).
    OR  → basta con que UN filtro se cumpla.
    Ejemplo OR: filtrar personas que sean imputadas O víctimas.

• "negate": false (default) | true
    Si true → NOT: excluye los registros que cumplan los filtros.
    Ejemplo: excluir causas en estado archivado.

• "same_entity": false (default) | true
    Si true → SAME_ENTITY: todos los filtros deben cumplirse sobre el MISMO
    sub-elemento de una lista anidada. Usar cuando la consulta exige que UNA
    SOLA entidad cumpla simultáneamente TODAS las condiciones.
    Ejemplo: "el imputado Martín Sosa que además está detenido" → same_entity=true
    sobre [vinculos.descripcion_vinculo=imputado, nombre_completo=Martin Sosa, es_detenido=true].
    SIN same_entity el motor podría tomar tres personas distintas y dar falso positivo.

    ══ REGLA ABSOLUTA DE SAME_ENTITY ══
    Una consulta sobre UNA entidad = UN SOLO step con same_entity=true.
    TODOS los filtros de esa entidad van juntos en ese step, sin excepción.
    NUNCA generes un segundo step con filtros que ya están en el SAME_ENTITY.
    NUNCA dividas los filtros de la misma entidad en dos steps.

    ❌ MAL — consulta "Martín Sosa imputado, domicilio en Goya, detenido":
    step1: same_entity=true, filters=[imputado, Sosa, detenido]
    step2: filters=[Sosa, Goya]   ← PROHIBIDO, Sosa ya está en step1

    ✅ BIEN — misma consulta:
    step1: same_entity=true, filters=[imputado, Sosa, detenido, Goya]  ← todo junto, un step

CUÁNDO USAR CADA OPERADOR:
  OR:          "víctima o querellante", "actor o demandado", "cualquiera de los roles"
  NOT:         "que no esté archivado", "que no sea menor", "excluir imputados"
  SAME_ENTITY: "el imputado X que además tiene domicilio en Y",
               "la víctima menor que además está detenida",
               "mismo [rol + nombre + condición adicional] sobre una persona"

REGLA ANTI-REDUNDANCIA — OBLIGATORIA:
  Antes de generar el plan, verificá: ¿algún filtro de un step nuevo repite
  información que ya está en otro step? Si sí → no generes ese step, fusionalo.
  Un mismo campo (nombre, rol, ciudad) NUNCA debe aparecer en dos steps distintos
  si ambos hablan de la misma entidad.
  Cantidad correcta de steps = cantidad de ENTIDADES DISTINTAS en la consulta.
  "Martín Sosa imputado en Goya detenido" → 1 entidad → 1 step.
  "Martín Sosa imputado + víctima menor" → 2 entidades → 2 steps.

REGLAS DE output_paths:
1. Incluir SOLO los paths que respondan directamente la consulta del usuario.
2. Elegir paths EXACTAMENTE del listado "Paths disponibles" de la función — no abreviar ni inventar nombres.
3. Siempre incluir "nombre_completo" cuando la entidad es persona, abogado o funcionario.
4. Siempre incluir "vinculos" si el filtro fue por vinculo o la consulta pide el rol.
5. Si la consulta pide domicilio/dirección: incluir los sub-campos relevantes (provincia, ciudad, calle), no el objeto domicilios completo.
6. Si la consulta pide contacto (celular/email): incluir digital_clase + descripcion.
7. Siempre copiar el nombre del path tal como aparece en "Paths disponibles". Ejemplos correctos: "ubicacion_actual_codigo", "ubicacion_actual_descripcion". NUNCA abreviar a "ubicacion_actual".
8. No incluir paths que el usuario no pidió (ej: si pide DNI, no incluir fecha_nacimiento).

══════════════════════════════════════════════════════════
 REGLAS ESPECIALES DE DESAMBIGUACIÓN
══════════════════════════════════════════════════════════

REGLA — "abogado de la víctima / del imputado":
  El abogado de una persona está en personas_legajo.relacionados.
  Usar get_abogados_de_persona con filtro vinculos.descripcion_vinculo.
  NO usar get_abogados — esa función trae abogados globales, no embebidos en personas.

REGLA — "celular/teléfono/email del abogado de la víctima":
  Usar get_contactos_abogados_de_persona con filtro vinculos.descripcion_vinculo + domicilios.digital_clase.

REGLA — "mayor de edad / no es menor":
  "mayor de edad" equivale a es_menor=false. Usar get_caracteristicas_personas
  con filtro {{"field": "caracteristicas.es_menor", "op": "eq", "value": "false"}}.
  NO usar fecha_nacimiento ni otro campo.

REGLA — consulta con domicilio + otras condiciones (nombre, rol, detenido):
  Si la consulta mezcla domicilio ("vive en X", "domicilio en Y") con otras condiciones
  sobre la MISMA persona (nombre, rol, es_detenido), usar SIEMPRE get_domicilios_personas.
  get_domicilios_personas tiene: vinculos, nombre_completo, es_detenido Y domicilios.
  NO usar get_caracteristicas_personas cuando hay filtro de domicilio — esa función
  no tiene el campo domicilios y el filtro de ciudad/provincia se perderá.

REGLA — nombres de personas en consultas sobre causa/delito/etapa:
  causa.descripcion es un texto libre CORTO (ej: "robo en poblado"). NO contiene nombres.
  causa.nivel_acceso_descripcion es un campo de acceso, NO es la etapa procesal.
  NUNCA filtres nombres de personas en causa, materia_delitos ni cabecera_legajo.

  Cuando la consulta mezcla nombres de personas con datos de causa/delito/etapa,
  siempre generá steps SEPARADOS:
    - Nombres/roles de personas  → get_personas (o get_domicilios_personas si hay domicilio)
    - Delito/descripcion causa   → get_delitos o get_causa
    - Etapa procesal / estado    → get_cabecera

  Roles procesales como "actor", "demandado", "querellante", "imputado", "victima"
  SIEMPRE se buscan en personas_legajo.vinculos.descripcion_vinculo.
  NUNCA en causa.descripcion.

  ❌ MAL — "causas de Manuel contra Thiago por explotación laboral en fase de prueba":
  step1: get_causa, filters=[descripcion contains Manuel, descripcion contains Thiago, ...]

  ✅ BIEN — misma consulta:
  step1: get_personas, same_entity=true, filters=[nombre_completo contains Manuel, vinculos=actor]
  step2: get_personas, same_entity=true, filters=[nombre_completo contains Thiago, vinculos=demandado]
  step3: get_delitos, filters=[descripcion contains explotacion laboral]
  step4: get_cabecera, filters=[etapa_procesal_descripcion contains prueba]

REGLA — "todos los celulares del expediente":
  Lanzar steps INDEPENDIENTES (sin depends_on) para:
  - get_domicilios_personas (filtro domicilios.digital_clase = Celular)
  - get_domicilios_abogados (filtro domicilios.digital_clase = Celular)
  - get_funcionarios (sin filtro, los funcionarios solo tienen email)

REGLA — "iurixweb", "THEMIS", "iurixcl", "criminis":
  Estas palabras son VALORES del campo codigo_sistema en los datos técnicos del legajo (_root).
  Si el usuario menciona cualquiera de ellas (ej: "de qué sistema es", "es de THEMIS",
  "viene de iurixweb"), agregar un step get_datos_sistema.
  Si el usuario pregunta si el legajo es de un sistema específico, filtrar:
    {{"field": "codigo_sistema", "op": "eq", "value": "THEMIS"}} (o el que corresponda).
  NO confundir con datos del expediente (cabecera_legajo) ni con dependencias.

  ══ REGLA CRÍTICA — sistemas + personas en la MISMA consulta ══
  Si la consulta menciona TANTO sistemas (iurixweb, THEMIS, etc.) COMO personas
  (nombres, víctimas, imputados, etc.), debés generar steps SEPARADOS e INDEPENDIENTES:
    - Un step get_datos_sistema para el sistema (filter_op=OR si hay más de uno).
    - Steps adicionales get_personas (u otras) para cada persona o rol mencionado.
  NUNCA ignorar las personas por el hecho de que haya un sistema mencionado.
  NUNCA ignorar el sistema por el hecho de que haya personas mencionadas.

  ❌ MAL — "expedientes de Thiago y José en iurixweb y criminis":
  step1: get_datos_sistema, filters=[codigo_sistema=iurixweb AND codigo_sistema=criminis]
  ← FALLA DOBLE: (1) ignora a Thiago y José, (2) AND en el mismo campo es imposible

  ✅ BIEN — misma consulta:
  step1: get_personas, filters=[nombre_completo contains Thiago]
  step2: get_personas, filters=[nombre_completo contains José]
  step3: get_datos_sistema, filter_op=OR, filters=[codigo_sistema=iurixweb, codigo_sistema=criminis]

  ══ REGLA — múltiples sistemas: SIEMPRE usar filter_op=OR ══
  Un mismo expediente solo puede pertenecer a UN sistema a la vez.
  "en iurixweb y criminis" significa "en iurixweb O en criminis" → filter_op=OR.
  NUNCA usar AND para dos valores del mismo campo codigo_sistema.

REGLA — distinguir PERSONA vs ABOGADO vs FUNCIONARIO:
  Si el usuario pregunta por "personas", "involucrados", "víctimas", "imputados"
    → get_personas (dominio personas_legajo).
  Si el usuario pregunta por "abogados", "defensores", "matrícula"
    → get_abogados (dominio abogados_legajo).
  Si el usuario pregunta por "fiscal", "juez", "secretario", "cargo"
    → get_funcionarios (dominio funcionarios).
  NUNCA mezclar: un imputado NO es un abogado. Un fiscal NO es una persona del expediente.
  Un abogado NO es un funcionario.

REGLA — distinguir CABECERA vs CAUSA vs DATOS_SISTEMA:
  - "estado del expediente", "etapa procesal", "CUIJ", "carátula", "prioridad", "organismo"
    → get_cabecera (dominio cabecera_legajo).
  - "qué pasó", "descripción del hecho", "fecha del hecho", "cómo se inició la causa"
    → get_causa (dominio causa).
  - "de qué sistema es", "servidor", "base de datos", "iurixweb", "THEMIS", "clave interna"
    → get_datos_sistema (dominio _root).
  NUNCA busques datos técnicos en cabecera ni datos administrativos en _root.

══════════════════════════════════════════════════════════
 ESTRUCTURA DEL PLAN
══════════════════════════════════════════════════════════
{{
  "steps": [
    {{
      "step_id": 1,
      "function": "nombre_funcion",
      "filter_op": "AND",
      "negate": false,
      "same_entity": false,
      "filters": [
        {{"field": "campo", "op": "operador", "value": "valor"}}
      ],
      "output_paths": ["path1", "path2"]
    }}
  ]
}}

══════════════════════════════════════════════════════════
 EJEMPLOS
══════════════════════════════════════════════════════════

"indicame que persona vive en Corrientes Capital"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_personas",
  "filters": [
    {{"field": "domicilios.domicilio.provincia", "op": "eq", "value": "CORRIENTES"}},
    {{"field": "domicilios.domicilio.ciudad", "op": "eq", "value": "CAPITAL"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "domicilios.domicilio.provincia", "domicilios.domicilio.ciudad", "domicilios.domicilio.calle"]
}}]}}

"DNI del abogado Thiago"
{{"steps": [{{"step_id": 1, "function": "get_abogados",
  "filters": [{{"field": "nombre", "op": "contains", "value": "Thiago"}}],
  "output_paths": ["nombre_completo", "numero_documento"]
}}]}}

"información del expediente"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": [],
  "output_paths": ["cuij", "numero_expediente", "anio_expediente", "tipo_expediente", "estado_expediente_descripcion", "caratula_publica", "etapa_procesal_descripcion", "organismo_descripcion", "ubicacion_actual_codigo", "ubicacion_actual_descripcion"]
}}]}}

"traeme las víctimas"
{{"steps": [{{"step_id": 1, "function": "get_personas",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}],
  "output_paths": ["nombre_completo", "numero_documento", "vinculos"]
}}]}}

"mostrame todos los abogados"
{{"steps": [{{"step_id": 1, "function": "get_abogados", "filters": [],
  "output_paths": ["nombre_completo", "numero_documento", "matricula", "vinculo_descripcion"]
}}]}}

"ficha del fiscal"
{{"steps": [{{"step_id": 1, "function": "get_funcionarios",
  "filters": [{{"field": "cargo", "op": "contains", "value": "fiscal"}}],
  "output_paths": ["nombre_completo", "numero_documento", "cargo"]
}}]}}

"DNI del abogado de la víctima"
{{"steps": [{{"step_id": 1, "function": "get_abogados_de_persona",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}],
  "output_paths": ["nombre_completo", "vinculos", "relacionados.nombre_completo", "relacionados.numero_documento"]
}}]}}

"celular del abogado de la víctima"
{{"steps": [{{"step_id": 1, "function": "get_contactos_abogados_de_persona",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}},
    {{"field": "relacionados.domicilios.digital_clase", "op": "contains", "value": "Celular"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "relacionados.nombre_completo", "relacionados.domicilios.digital_clase", "relacionados.domicilios.descripcion"]
}}]}}

"celular del defensor público"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_abogados",
  "filters": [
    {{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}},
    {{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}
  ],
  "output_paths": ["nombre_completo", "vinculo_descripcion", "domicilios.digital_clase", "domicilios.descripcion"]
}}]}}

"a quién representa el defensor público?"
{{"steps": [{{"step_id": 1, "function": "get_representados_abogados",
  "filters": [{{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}}],
  "output_paths": ["nombre_completo", "vinculo_descripcion", "representados.nombre_completo", "representados.vinculo_descripcion"]
}}]}}

"domicilios de las víctimas"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_personas",
  "filters": [{{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}}],
  "output_paths": ["nombre_completo", "vinculos", "domicilios.domicilio.provincia", "domicilios.domicilio.ciudad", "domicilios.domicilio.calle"]
}}]}}

"características de los imputados detenidos"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "imputado"}},
    {{"field": "es_detenido", "op": "eq", "value": "true"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "es_detenido", "caracteristicas.ocupacion", "caracteristicas.estado_civil", "caracteristicas.es_menor"]
}}]}}

"la víctima es mayor de edad?"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}},
    {{"field": "caracteristicas.es_menor", "op": "eq", "value": "false"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "caracteristicas.es_menor"]
}}]}}

"todos los celulares del expediente"
{{"steps": [
  {{"step_id": 1, "function": "get_domicilios_personas",
   "filters": [{{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}],
   "output_paths": ["nombre_completo", "vinculos", "domicilios.digital_clase", "domicilios.descripcion"]}},
  {{"step_id": 2, "function": "get_domicilios_abogados",
   "filters": [{{"field": "domicilios.digital_clase", "op": "contains", "value": "Celular"}}],
   "output_paths": ["nombre_completo", "vinculo_descripcion", "domicilios.digital_clase", "domicilios.descripcion"]}},
  {{"step_id": 3, "function": "get_funcionarios", "filters": [],
   "output_paths": ["nombre_completo", "cargo", "domicilios"]}}
]}}

"domicilio del representado del defensor público"
{{"steps": [
  {{"step_id": 1, "function": "get_representados_abogados",
   "filters": [{{"field": "vinculo_descripcion", "op": "contains", "value": "defensor publico"}}],
   "output_paths": ["nombre_completo", "vinculo_descripcion", "representados.nombre_completo", "representados.numero_documento"]}},
  {{"step_id": 2, "function": "get_domicilios_personas", "filters": [], "depends_on": 1,
   "output_paths": ["nombre_completo", "domicilios.domicilio.provincia", "domicilios.domicilio.ciudad", "domicilios.domicilio.calle"]}}
]}}

"cuál es el CUIJ?"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": [],
  "output_paths": ["cuij", "numero_expediente", "anio_expediente"]
}}]}}

"descripción de la causa"
{{"steps": [{{"step_id": 1, "function": "get_causa", "filters": [],
  "output_paths": ["descripcion", "fecha_hecho", "forma_inicio", "caratula_publica"]
}}]}}

"delitos del expediente"
{{"steps": [{{"step_id": 1, "function": "get_delitos", "filters": [],
  "output_paths": ["codigo", "descripcion"]
}}]}}

"radicaciones del expediente"
{{"steps": [{{"step_id": 1, "function": "get_radicaciones", "filters": [],
  "output_paths": ["organismo_actual_codigo", "organismo_actual_descripcion", "fecha_desde", "fecha_hasta", "motivo_actual_descripcion"]
}}]}}

"dependencias que intervinieron"
{{"steps": [{{"step_id": 1, "function": "get_dependencias", "filters": [],
  "output_paths": ["organismo_descripcion", "dependencia_descripcion", "clase_descripcion", "rol", "activo"]
}}]}}

"dónde está radicado el expediente?"
{{"steps": [{{"step_id": 1, "function": "get_cabecera", "filters": [],
  "output_paths": ["ubicacion_actual_codigo", "ubicacion_actual_descripcion", "dependencia_radicacion_codigo", "dependencia_radicacion_descripcion"]
}}]}}

"personas que sean víctimas o querellantes"
{{"steps": [{{"step_id": 1, "function": "get_personas",
  "filter_op": "OR",
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}},
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "querellante"}}
  ],
  "output_paths": ["nombre_completo", "numero_documento", "vinculos"]
}}]}}

"causas que no estén archivadas"
{{"steps": [{{"step_id": 1, "function": "get_cabecera",
  "negate": true,
  "filters": [{{"field": "estado_expediente_descripcion", "op": "contains", "value": "archivado"}}],
  "output_paths": ["cuij", "numero_expediente", "estado_expediente_descripcion", "etapa_procesal_descripcion"]
}}]}}

"causas de Manuel contra Thiago por explotación laboral en fase de prueba"
{{"steps": [
  {{"step_id": 1, "function": "get_personas",
   "same_entity": true,
   "filters": [
     {{"field": "nombre_completo", "op": "contains", "value": "Manuel"}},
     {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "actor"}}
   ],
   "output_paths": ["nombre_completo", "vinculos", "numero_documento"]}},
  {{"step_id": 2, "function": "get_personas",
   "same_entity": true,
   "filters": [
     {{"field": "nombre_completo", "op": "contains", "value": "Thiago"}},
     {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "demandado"}}
   ],
   "output_paths": ["nombre_completo", "vinculos", "numero_documento"]}},
  {{"step_id": 3, "function": "get_delitos",
   "filters": [{{"field": "descripcion", "op": "contains", "value": "explotacion laboral"}}],
   "output_paths": ["codigo", "descripcion"]}},
  {{"step_id": 4, "function": "get_cabecera",
   "filters": [{{"field": "etapa_procesal_descripcion", "op": "contains", "value": "prueba"}}],
   "output_paths": ["cuij", "numero_expediente", "etapa_procesal_descripcion", "estado_expediente_descripcion"]}}
]}}

"el imputado Martín Sosa que está detenido"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "same_entity": true,
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "imputado"}},
    {{"field": "nombre_completo", "op": "contains", "value": "Martin Sosa"}},
    {{"field": "es_detenido", "op": "eq", "value": "true"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "es_detenido", "caracteristicas.ocupacion"]
}}]}}

"Martin Sosa figure como imputado, tenga domicilio en Goya y esté detenido"
{{"steps": [{{"step_id": 1, "function": "get_domicilios_personas",
  "same_entity": true,
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "imputado"}},
    {{"field": "nombre_completo", "op": "contains", "value": "Martin Sosa"}},
    {{"field": "es_detenido", "op": "eq", "value": "true"}},
    {{"field": "domicilios.domicilio.ciudad", "op": "eq", "value": "GOYA"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "es_detenido", "domicilios.domicilio.provincia", "domicilios.domicilio.ciudad", "domicilios.domicilio.calle"]
}}]}}

"víctima menor que no esté detenida"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "same_entity": true,
  "negate": false,
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "victima"}},
    {{"field": "caracteristicas.es_menor", "op": "eq", "value": "true"}},
    {{"field": "es_detenido", "op": "eq", "value": "false"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "caracteristicas.es_menor", "es_detenido"]
}}]}}

"de qué sistema viene este legajo?"
{{"steps": [{{"step_id": 1, "function": "get_datos_sistema", "filters": [],
  "output_paths": ["codigo_sistema", "base_datos", "servidor"]
}}]}}

"es de THEMIS este expediente?"
{{"steps": [{{"step_id": 1, "function": "get_datos_sistema",
  "filters": [{{"field": "codigo_sistema", "op": "eq", "value": "THEMIS"}}],
  "output_paths": ["codigo_sistema", "base_datos"]
}}]}}

"dame los datos de iurixweb"
{{"steps": [{{"step_id": 1, "function": "get_datos_sistema",
  "filters": [{{"field": "codigo_sistema", "op": "eq", "value": "iurixweb"}}],
  "output_paths": ["codigo_sistema", "base_datos", "servidor", "estado"]
}}]}}

"quién es el juez del expediente?"
{{"steps": [{{"step_id": 1, "function": "get_funcionarios",
  "filters": [{{"field": "cargo", "op": "contains", "value": "juez"}}],
  "output_paths": ["nombre_completo", "cargo", "numero_documento"]
}}]}}

"ocupación del imputado detenido"
{{"steps": [{{"step_id": 1, "function": "get_caracteristicas_personas",
  "same_entity": true,
  "filters": [
    {{"field": "vinculos.descripcion_vinculo", "op": "contains", "value": "imputado"}},
    {{"field": "es_detenido", "op": "eq", "value": "true"}}
  ],
  "output_paths": ["nombre_completo", "vinculos", "es_detenido", "caracteristicas.ocupacion"]
}}]}}

"organismo de control del expediente"
{{"steps": [{{"step_id": 1, "function": "get_organismo_control", "filters": [],
  "output_paths": ["organismo_codigo", "organismo_descripcion"]
}}]}}

"expedientes donde aparezcan Thiago y José en el sistema iurixweb y criminis"
{{"steps": [
  {{"step_id": 1, "function": "get_personas",
   "filters": [{{"field": "nombre_completo", "op": "contains", "value": "Thiago"}}],
   "output_paths": ["nombre_completo", "vinculos", "numero_documento"]}},
  {{"step_id": 2, "function": "get_personas",
   "filters": [{{"field": "nombre_completo", "op": "contains", "value": "José"}}],
   "output_paths": ["nombre_completo", "vinculos", "numero_documento"]}},
  {{"step_id": 3, "function": "get_datos_sistema",
   "filter_op": "OR",
   "filters": [
     {{"field": "codigo_sistema", "op": "eq", "value": "iurixweb"}},
     {{"field": "codigo_sistema", "op": "eq", "value": "criminis"}}
   ],
   "output_paths": ["codigo_sistema", "base_datos", "servidor"]}}
]}}

SOLO devuelve JSON."""


_USER_TEMPLATE = "Consulta: {prompt}"


# ═══════════════════════════════════════════════════════════════
#  Parsing de la respuesta del LLM
# ═══════════════════════════════════════════════════════════════

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_llm_json(raw: str) -> Dict[str, Any]:
    """Intenta parsear JSON de la respuesta del LLM."""
    # 1. Bloques de código
    m = _JSON_BLOCK_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Primer JSON object
    m = _JSON_OBJECT_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 3. Directo
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {}


def _validate_step(step_dict: Dict[str, Any]) -> Optional[Step]:
    """Valida que un step tenga función válida y lo construye."""
    func_name = step_dict.get("function", "")
    if func_name not in FUNCTION_CATALOG:
        print(f"[llm_planner] Función desconocida: {func_name}")
        return None

    # Parsear filtros
    filters = []
    for f in step_dict.get("filters", []):
        if isinstance(f, dict) and "field" in f and "value" in f:
            filters.append(StepFilter(
                field=f["field"],
                op=f.get("op", "contains"),
                value=str(f["value"]),
            ))

    # Parsear output_paths (opcional)
    raw_paths = step_dict.get("output_paths")
    output_paths: Optional[List[str]] = None
    if isinstance(raw_paths, list) and raw_paths and raw_paths != ["*"]:
        # Validar contra los paths disponibles de la función
        available = set(FUNCTION_AVAILABLE_PATHS.get(func_name, []))
        if available and available != {"*"}:
            valid = [p for p in raw_paths if p in available]
            output_paths = valid if valid else None
        else:
            output_paths = raw_paths  # función escalar o sin restricción

    return Step(
        step_id=step_dict.get("step_id", 0),
        function=func_name,
        filters=filters,
        filter_op=step_dict.get("filter_op", "AND").upper(),
        negate=bool(step_dict.get("negate", False)),
        same_entity=bool(step_dict.get("same_entity", False)),
        output_paths=output_paths,
        depends_on=step_dict.get("depends_on"),
    )


# ═══════════════════════════════════════════════════════════════
#  API principal
# ═══════════════════════════════════════════════════════════════

def generate_plan_with_llm(user_prompt: str) -> Plan:
    """
    Usa OpenAI para generar un plan de funciones semánticas.

    El system prompt se envía como rol 'system' para que OpenAI lo cachee
    automáticamente (ahorro de hasta ~50 % en tokens de entrada cuando el
    prefijo supera los ~1 024 tokens).

    Returns:
        Plan con steps semánticos.
    """
    from classes.custom_llm_classes import get_llm
    llm = get_llm()
    llm.system_prompt = _SYSTEM_PROMPT   # ← cacheado por OpenAI en llamadas repetidas

    user_text = _USER_TEMPLATE.format(prompt=user_prompt)

    print(f"\n[llm_planner] 🔍 Consulta del usuario: '{user_prompt}'")
    print(f"[llm_planner] 🤖 Modelo: {llm.model}  |  temp={llm.temperature}  |  max_tokens={llm.max_tokens}")

    try:
        raw_response = llm._call(prompt=user_text, stop=None)
    except Exception as e:
        print(f"[llm_planner] ❌ LLM error: {e}")
        return Plan(steps=[])

    parsed = _parse_llm_json(raw_response)
    if not parsed:
        print(f"[llm_planner] No se pudo parsear: {raw_response[:300]}")
        return Plan(steps=[])

    # Construir steps
    steps = []
    raw_steps = parsed.get("steps", [])
    for s in raw_steps:
        if isinstance(s, dict):
            step = _validate_step(s)
            if step:
                steps.append(step)

    if not steps:
        print("[llm_planner] Plan sin steps válidos")
        return Plan(steps=[])

    return Plan(steps=steps)
