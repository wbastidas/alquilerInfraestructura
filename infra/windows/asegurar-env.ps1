# Restringe los permisos del archivo backend\.env (secretos: JWT_SECRET_KEY,
# AES_MASTER_KEY, credenciales de BD) para que solo la cuenta de servicio y los
# administradores puedan leerlo, segun §3.3/§4 de la especificacion tecnica.
#
# Uso (PowerShell como Administrador):
#   .\asegurar-env.ps1 -RutaEnv "C:\SGAIE\alquilerInfraestructura\backend\.env" -CuentaServicio "NT SERVICE\SGAIE-Backend"

param(
    [Parameter(Mandatory = $true)]
    [string]$RutaEnv,
    [string]$CuentaServicio = "NT AUTHORITY\SYSTEM"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RutaEnv)) {
    throw "No se encontro el archivo '$RutaEnv'."
}

Write-Host "==> Deshabilitando herencia de permisos en '$RutaEnv'..." -ForegroundColor Cyan
icacls $RutaEnv /inheritance:r

Write-Host "==> Otorgando acceso de lectura solo a Administradores y a '$CuentaServicio'..." -ForegroundColor Cyan
icacls $RutaEnv /grant:r "BUILTIN\Administrators:(R)"
icacls $RutaEnv /grant:r "$CuentaServicio`:(R)"

Write-Host "==> Permisos finales:" -ForegroundColor Green
icacls $RutaEnv
