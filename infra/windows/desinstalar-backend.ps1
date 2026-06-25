# Detiene y elimina el servicio de Windows del backend de SGAIE (registrado con NSSM).
# No borra el repositorio, el entorno virtual ni la base de datos: solo el servicio.
#
# Uso (PowerShell como Administrador):
#   .\desinstalar-backend.ps1 -RutaNssm "C:\nssm\nssm.exe"

param(
    [string]$RutaNssm = "C:\nssm\nssm.exe",
    [string]$NombreServicio = "SGAIE-Backend"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RutaNssm)) {
    throw "No se encontro nssm.exe en '$RutaNssm'. Ajuste -RutaNssm."
}

Write-Host "==> Deteniendo el servicio '$NombreServicio' (si esta en ejecucion)..." -ForegroundColor Cyan
& $RutaNssm stop $NombreServicio 2>&1 | Out-Null

Write-Host "==> Eliminando el servicio '$NombreServicio'..." -ForegroundColor Cyan
& $RutaNssm remove $NombreServicio confirm

Write-Host "Servicio eliminado." -ForegroundColor Green
