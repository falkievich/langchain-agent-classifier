# syntax=docker/dockerfile:1
# Habilitar BuildKit para usar cache mounts y acelerar builds

# ============================================================
# IMAGEN BASE
# ============================================================
FROM python:3.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ============================================================
# CAPA 1: DEPENDENCIAS DEL SISTEMA
# ============================================================
# Instalar dependencias del sistema si son necesarias (git, curl, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# CAPA 2: DEPENDENCIAS DE PYTHON (SE CACHEA)
# ============================================================
# Copiar SOLO requirements.txt primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python con:
# - Cache mount persistente (no se pierde entre builds)
# - Reintentos automáticos (--retries 10)
# - Timeout largo (--timeout 180 = 3 minutos por paquete)
# - NO usar --no-cache-dir para que pip guarde los paquetes descargados
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --upgrade pip && \
    pip install \
        --retries 10 \
        --timeout 180 \
        --default-timeout=180 \
        -r requirements.txt

# Verificar que las dependencias críticas se instalaron correctamente
RUN python -c "import fastapi; print('✅ FastAPI instalado')" && \
    python -c "import langchain; print('✅ LangChain instalado')" && \
    python -c "import dotenv; print('✅ python-dotenv instalado')"

# ============================================================
# CAPA 3: CÓDIGO DE LA APLICACIÓN (se invalida con cada cambio)
# ============================================================
# Copiar TODO el código de la aplicación AL FINAL
# Esto permite que los cambios de código no invaliden el cache de dependencias
COPY . .

# ============================================================
# CONFIGURACIÓN FINAL
# ============================================================
# Exponer el puerto en el que corre FastAPI
EXPOSE 8000

# Health check para verificar que la aplicación está corriendo
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/extract-persons/health || exit 1

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
