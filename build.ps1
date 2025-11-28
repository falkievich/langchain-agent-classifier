# Script para construir la imagen Docker con BuildKit habilitado y reintentos automáticos
# Esto permite usar cache mounts que persisten incluso si alguna descarga falla

Write-Host "🚀 Construyendo imagen Docker de langchain-agent-classifier..." -ForegroundColor Cyan
Write-Host "📦 Con cache optimizado y reintentos automáticos para redes restrictivas" -ForegroundColor Yellow
Write-Host ""

# Habilitar BuildKit (cache persistente, mejor rendimiento)
$env:DOCKER_BUILDKIT=1
$env:COMPOSE_DOCKER_CLI_BUILD=1

Write-Host "🔧 BuildKit habilitado (cache persistente activado)" -ForegroundColor Green
Write-Host ""

# Construir con docker-compose (usa BuildKit automáticamente)
Write-Host "🏗️  Iniciando build..." -ForegroundColor Cyan
docker-compose build --progress=plain

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "="*70 -ForegroundColor Green
    Write-Host "✅ BUILD COMPLETADO EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "="*70 -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Próximos pasos:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1️⃣  Iniciar el contenedor:" -ForegroundColor White
    Write-Host "      docker-compose up -d" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2️⃣  Ver logs en tiempo real:" -ForegroundColor White
    Write-Host "      docker-compose logs -f" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3️⃣  Verificar el health check:" -ForegroundColor White
    Write-Host "      curl http://localhost:8000/api/extract-persons/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  4️⃣  Detener el contenedor:" -ForegroundColor White
    Write-Host "      docker-compose down" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "="*70 -ForegroundColor Red
    Write-Host "⚠️  BUILD FALLÓ" -ForegroundColor Red
    Write-Host "="*70 -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Posibles soluciones:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Si falló por timeout de red, intenta ejecutar nuevamente:" -ForegroundColor White
    Write-Host "     .\build.ps1" -ForegroundColor Cyan
    Write-Host "     (Las descargas exitosas están cacheadas y NO se repetirán)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. Si el error persiste, verifica tu conexión a internet" -ForegroundColor White
    Write-Host ""
    Write-Host "  3. Intenta construir sin cache (último recurso):" -ForegroundColor White
    Write-Host "     docker-compose build --no-cache --progress=plain" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  4. Ver logs detallados del error arriba ☝️" -ForegroundColor White
    Write-Host ""
}
