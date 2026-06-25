# Compila el frontend (Vite) y publica el resultado estatico en el webroot
# servido por IIS o Nginx para Windows (ver infra/nginx-or-iis).
#
# Uso (PowerShell):
#   .\publicar-frontend.ps1 -RutaRepo "C:\SGAIE\alquilerInfraestructura" -RutaWebroot "C:\inetpub\sgaie"

param(
    [string]$RutaRepo = "C:\SGAIE\alquilerInfraestructura",
    [string]$RutaWebroot = "C:\inetpub\sgaie"
)

$ErrorActionPreference = "Stop"

$rutaFrontend = Join-Path $RutaRepo "frontend"
$rutaDist = Join-Path $rutaFrontend "dist"

if (-not (Test-Path $rutaFrontend)) {
    throw "No se encontro la carpeta frontend en '$rutaFrontend'. Verifique -RutaRepo."
}

Write-Host "==> Instalando dependencias del frontend (pnpm)..." -ForegroundColor Cyan
Push-Location $rutaFrontend
try {
    pnpm install --frozen-lockfile
    Write-Host "==> Compilando build de produccion..." -ForegroundColor Cyan
    pnpm build
} finally {
    Pop-Location
}

if (-not (Test-Path $rutaDist)) {
    throw "La build no genero la carpeta '$rutaDist'. Revise la salida de 'pnpm build'."
}

Write-Host "==> Publicando en '$RutaWebroot'..." -ForegroundColor Cyan
if (-not (Test-Path $RutaWebroot)) {
    New-Item -ItemType Directory -Path $RutaWebroot | Out-Null
}
Copy-Item -Path (Join-Path $rutaDist "*") -Destination $RutaWebroot -Recurse -Force

Write-Host "Frontend publicado en '$RutaWebroot'." -ForegroundColor Green
