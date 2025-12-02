# Script para construir la imagen Docker con BuildKit habilitado y reintentos automáticos
# Esto permite usar cache mounts que persisten incluso si alguna descarga falla

# Forzar UTF-8 en PowerShell para evitar problemas de encoding/emoji en la salida
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

Write-Host "Construyendo imagen Docker de langchain-agent-classifier..." -ForegroundColor Cyan
Write-Host "Con cache optimizado y reintentos automáticos para redes restrictivas" -ForegroundColor Yellow
Write-Host ""

# Habilitar BuildKit (cache persistente, mejor rendimiento)
$env:DOCKER_BUILDKIT=1
$env:COMPOSE_DOCKER_CLI_BUILD=1

Write-Host "BuildKit habilitado (cache persistente activado)" -ForegroundColor Green
Write-Host ""

# Construir con docker-compose (usa BuildKit automáticamente)
Write-Host "Iniciando build..." -ForegroundColor Cyan
docker-compose build --progress=plain

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "" + "="*70 -ForegroundColor Green
    Write-Host "BUILD COMPLETADO EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "" + "="*70 -ForegroundColor Green
    Write-Host ""
    Write-Host "Proximos pasos:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1) Iniciar el contenedor:" -ForegroundColor White
    Write-Host "      docker-compose up -d" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2) Ver logs en tiempo real:" -ForegroundColor White
    Write-Host "      docker-compose logs -f" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3) Verificar el health check:" -ForegroundColor White
    Write-Host "      curl http://localhost:8000/api/extract-persons/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  4) Detener el contenedor:" -ForegroundColor White
    Write-Host "      docker-compose down" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "" + "="*70 -ForegroundColor Red
    Write-Host "BUILD FALLO" -ForegroundColor Red
    Write-Host "" + "="*70 -ForegroundColor Red
    Write-Host ""
    Write-Host "Posibles soluciones:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1) Si fallo por timeout de red, intenta ejecutar nuevamente:" -ForegroundColor White
    Write-Host "     .\build.ps1" -ForegroundColor Cyan
    Write-Host "     (Las descargas exitosas estan cacheadas y NO se repetiran)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2) Si el error persiste, verifica tu conexion a internet" -ForegroundColor White
    Write-Host ""
    Write-Host "  3) Intenta construir sin cache (ultimo recurso):" -ForegroundColor White
    Write-Host "     docker-compose build --no-cache --progress=plain" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  4) Ver logs detallados del error arriba" -ForegroundColor White
    Write-Host ""
}
