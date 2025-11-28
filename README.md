# LangChain Agent Classifier

> Sistema de agente inteligente basado en **LangChain** y **FastAPI** para procesamiento automatizado de expedientes judiciales mediante Large Language Models (LLM).

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](Dockerfile)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green?logo=fastapi)](app.py)

---

## 📋 Tabla de Contenidos

- [🚀 Quick Start](#-quick-start)
  - [Opción 1: Docker (Recomendado)](#opción-1-docker-recomendado)
  - [Opción 2: Ejecución Local](#opción-2-ejecución-local)
- [🏗️ Arquitectura](#arquitectura)
- [⚙️ Funcionalidades](#️-funcionalidades)
  - [1️⃣ Agente LLM con Tools](#1️⃣-agente-llm-con-tools)
  - [2️⃣ Extracción de Personas con LLM](#2️⃣-extracción-de-personas-con-llm)
- [🔐 Configuración](#configuración)


---

## 🚀 Quick Start

### Opción 1: Docker (Recomendado)

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd langchain-agent-classifier

# 2. Configurar .env (ver sección "Configuración")

# 3. Build y Start
docker-compose build
docker-compose up -d

# 4. Ver logs en tiempo real
docker-compose logs -f

# 5. Health check
curl http://localhost:8000/api/extract-persons/health

# 6. Detener contenedores
docker-compose down

```

### Opción 2: Local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env (ver sección "Configuración")

# 3. Ejecutar servidor
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 4. Health check
curl http://localhost:8000/api/extract-persons/health

```

---


---

## ⚙️ Funcionalidades

### 1️⃣ Agente LLM con Tools

> Sistema de agente inteligente que analiza expedientes judiciales y responde preguntas en lenguaje natural usando herramientas especializadas.

#### 📍 Endpoint

```http
POST /api/agent_llm
```

#### 📥 Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `user_prompt` | Form (string) | Pregunta en lenguaje natural |
| `json_file` | File | JSON con datos del expediente |

#### 🔄 Pipeline de Ejecución

```
Usuario
  ↓
┌─────────────────────────────────────────────────────────┐
│ 1. PREPARACIÓN (agent_service.py)                      │
│  • Cargar todas las tools disponibles                  │
│  • Inicializar LLM (MODEL_ID)                          │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 2. PLANNER (planning.py)                                │
│  • LLM analiza el prompt                                │
│  • Selecciona tools relevantes                          │
│  • Genera plan de ejecución:                            │
│    [{tool: "buscar_persona", args: ["rol", "Actor"]}]  │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 3. EXECUTOR (execution.py)                              │
│  • Ejecuta tools EN PARALELO                            │
│  • Consolida resultados                                 │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 4. FINALIZER (execution.py)                             │
│  • LLM sintetiza resultados                             │
│  • Responde en lenguaje natural                         │
└──────────────────────┬──────────────────────────────────┘
                       ↓
               Respuesta al Usuario
```

#### 🛠️ Tools Disponibles

<details>
<summary><b>Listados</b></summary>

- `listar_todo(dominio)` - Lista todos los elementos de un dominio
  - Dominios: `persona`, `abogado`, `expediente`, `radicacion`, `dependencia`, `delito`, `funcionario`, `causa`, `clasificador`

</details>

<details>
<summary><b>Búsquedas Globales</b></summary>

**Personas**
- `buscar_persona(filtro, valor)` - Búsqueda general
- `buscar_persona_por_nombre(nombre)` - Por nombre
- `buscar_persona_por_dni(dni)` - Por DNI
- `buscar_persona_por_rol(rol)` - Por rol

**Abogados**
- `buscar_abogado(filtro, valor)` - Búsqueda general
- `buscar_clientes_de_abogado(nombre_abogado)` - Clientes
- `buscar_abogado_por_cliente(nombre_cliente)` - Por cliente

**Expedientes**
- `buscar_expediente(filtro, valor)` - Búsqueda general
- `obtener_info_general_expediente()` - Info general

**Radicaciones**
- `buscar_radicacion(filtro, valor)` - Búsqueda general

**Dependencias**
- `buscar_dependencia(filtro, valor)` - Búsqueda general

</details>

<details>
<summary><b>Búsquedas por Dominio</b></summary>

- `buscar_en_dominio(dominio, filtro, valor)` - Búsqueda genérica

</details>

#### 📝 Ejemplo de Uso

**Request:**
```bash
curl -X POST http://localhost:8000/api/agent_llm \
  -F "user_prompt=¿Quién es el demandante y su abogado?" \
  -F "json_file=@expediente.json"
```

**Response:**
```json
{
  "response": "El demandante es Juan Pérez (DNI 12345678), representado por la abogada María López (Matrícula MP-2025-001)."
}
```

---

### 2️⃣ Extracción de Personas con LLM

> Sistema especializado que extrae y consolida automáticamente TODAS las personas mencionadas en un expediente judicial.

#### 📍 Endpoint

```http
POST /api/extract-persons-with-llm
```

#### 📥 Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `json_txt_file` | File | JSON o TXT con datos del expediente |

#### 🔄 Pipeline de Ejecución

```
Usuario
  ↓
┌─────────────────────────────────────────────────────────┐
│ 1. CARGA DEL JSON                                       │
│  • Lee el archivo                                       │
│  • Valida formato                                       │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 2. EXTRACCIÓN (person_extraction_service.py)            │
│  • Inicializa LLM (MODEL_ID_2)                          │
│  • Prompt especializado para extraer personas           │
│  • Busca en TODAS las secciones del JSON                │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 3. CONSOLIDACIÓN                                        │
│  • Identifica duplicados por:                           │
│    - DNI, CUIL, nombre_completo                         │
│  • Mezcla roles y datos                                 │
│  • Genera una entrada única por persona                 │
└──────────────────────┬──────────────────────────────────┘
                       ↓
         JSON Estructurado con Personas
```

#### ✨ Características

| Feature | Descripción |
|---------|-------------|
| ✅ **Consolidación Automática** | Detecta y fusiona personas duplicadas |
| ✅ **Extracción Exhaustiva** | Busca en TODAS las secciones del JSON |
| ✅ **Roles Múltiples** | Agrupa todos los roles de una persona |
| ✅ **Datos Completos** | Mezcla información de todas las fuentes |

#### 📝 Ejemplo de Consolidación

**Entrada:**
```json
{
  "personas_legajo": [
    {
      "nombre_completo": "María Pérez",
      "dni": "87654321",
      "rol": "DILIGENCIANTE",
      "genero": "FEMENINO"
    }
  ],
  "abogados_legajo": [
    {
      "nombre_completo": "María Pérez",
      "dni": "87654321",
      "matricula": "MP-2025-001"
    }
  ]
}
```

**Salida (Consolidada):**
```json
{
  "personas": [
    {
      "nombre_completo": "María Pérez",
      "roles": ["DILIGENCIANTE", "ABOGADO"],
      "datos_adicionales": {
        "dni": "87654321",
        "cuil": "27-87654321-9",
        "matricula": "MP-2025-001",
        "genero": "FEMENINO"
      }
    }
  ],
  "total": 1
}
```

#### 🩺 Health Check

```bash
curl http://localhost:8000/api/extract-persons/health
```

---

## 🔐 Configuración

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto con la siguiente estructura:

```bash
# ============================================================
# LLM Server Configuration
# ============================================================
BASE_URL=<url_del_servidor_llm>
API_KEY=<tu_api_key>

# ============================================================
# Model Configuration
# ============================================================
MODEL_ID=<modelo_principal>          # Modelo para agente con tools
MODEL_ID_2=<modelo_extraccion>       # Modelo para extracción de personas
SMALL_MODEL_ID=<modelo_pequeño>      # Modelo pequeño (uso futuro)

# ============================================================
# LangChain Observability (Opcional)
# ============================================================
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=<tu_langchain_api_key>
# LANGCHAIN_PROJECT=langchain-agent-classifier
```

**Ejemplo de configuración:**
- `BASE_URL`: URL completa del servidor LLM compatible con OpenAI API (ej: `http://servidor:puerto/api/chat/completions`)
- `API_KEY`: Clave de autenticación del servidor LLM
- `MODEL_ID`: Nombre del modelo LLM para el agente (ej: `gpt-oss:20b`, `llama2:13b`)
- `MODEL_ID_2`: Nombre del modelo LLM para extracción de personas
- `SMALL_MODEL_ID`: Modelo pequeño para optimizaciones futuras

### Endpoints

| Endpoint | Method | Descripción |
|----------|--------|-------------|
| `/api/agent_llm` | POST | Agente LLM con tools |
| `/api/extract-persons-with-llm` | POST | Extracción de personas |
| `/api/extract-persons/health` | GET | Health check |

---

