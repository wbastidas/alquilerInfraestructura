# Instala el backend de SGAIE como servicio de Windows (NSSM) en Windows Server.
#
# Requisitos previos en el servidor:
#   - Python 3.12+ instalado y en el PATH.
#   - MariaDB 11.x instalado y en ejecucion (servicio de Windows nativo).
#   - NSSM descargado (https://nssm.cc/) y la ruta a nssm.exe disponible.
#
# Uso (PowerShell como Administrador):
#   .\instalar-backend.ps1 -RutaRepo "C:\SGAIE\alquilerInfraestructura" -RutaNssm "C:\nssm\nssm.exe"
#
# El script es idempotente: puede ejecutarse de nuevo tras un `git pull` para
# actualizar dependencias y reiniciar el servicio.

param(
    [string]$RutaRepo = "C:\SGAIE\alquilerInfraestructura",
    [string]$RutaNssm = "C:\nssm\nssm.exe",
    [string]$NombreServicio = "SGAIE-Backend",
    [string]$HostBind = "127.0.0.1",
    [int]$Puerto = 8000,
    [int]$Workers = 4
)

$ErrorActionPreference = "Stop"

function Asegurar-Administrador {
    $identidad = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identidad)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Este script debe ejecutarse en una consola de PowerShell con privilegios de Administrador."
    }
}

Asegurar-Administrador

$rutaBackend = Join-Path $RutaRepo "backend"
$rutaVenv = Join-Path $rutaBackend ".venv"
$rutaPython = Join-Path $rutaVenv "Scripts\python.exe"
$rutaEnv = Join-Path $rutaBackend ".env"
$rutaEnvEjemplo = Join-Path $rutaBackend ".env.example"
$rutaLogs = Join-Path $rutaBackend "logs"

if (-not (Test-Path $rutaBackend)) {
    throw "No se encontro la carpeta backend en '$rutaBackend'. Verifique -RutaRepo."
}

Write-Host "==> Verificando version de Python..." -ForegroundColor Cyan
$versionPython = (python --version) 2>&1
Write-Host "    $versionPython"

Write-Host "==> Creando entorno virtual (si no existe)..." -ForegroundColor Cyan
if (-not (Test-Path $rutaVenv)) {
    python -m venv $rutaVenv
}

Write-Host "==> Instalando dependencias del backend..." -ForegroundColor Cyan
& $rutaPython -m pip install --upgrade pip
& $rutaPython -m pip install -e $rutaBackend

if (-not (Test-Path $rutaEnv)) {
    Write-Host "==> No existe backend\.env: copiando desde .env.example." -ForegroundColor Yellow
    Copy-Item $rutaEnvEjemplo $rutaEnv
    Write-Host "    IMPORTANTE: edite '$rutaEnv' con los valores reales (BD, JWT_SECRET_KEY," -ForegroundColor Yellow
    Write-Host "    AES_MASTER_KEY, LDAP, CORS_ORIGENS) antes de continuar." -ForegroundColor Yellow
    Write-Host "    Luego proteja el archivo con ACL restrictivas (ver paso 'Asegurar .env' abajo)." -ForegroundColor Yellow
}

Write-Host "==> Aplicando migraciones de base de datos (Alembic)..." -ForegroundColor Cyan
Push-Location $rutaBackend
try {
    & $rutaPython -m alembic upgrade head
} finally {
    Pop-Location
}

if (-not (Test-Path $rutaLogs)) {
    New-Item -ItemType Directory -Path $rutaLogs | Out-Null
}

if (-not (Test-Path $RutaNssm)) {
    throw "No se encontro nssm.exe en '$RutaNssm'. Descarguelo de https://nssm.cc/ y ajuste -RutaNssm."
}

$servicioExiste = (& $RutaNssm status $NombreServicio) 2>&1
if ($LASTEXITCODE -ne 0 -or $servicioExiste -match "SERVICE_NOT_FOUND") {
    Write-Host "==> Registrando el servicio de Windows '$NombreServicio'..." -ForegroundColor Cyan
    $argumentosUvicorn = "-m uvicorn app.main:app --host $HostBind --port $Puerto --workers $Workers"
    & $RutaNssm install $NombreServicio $rutaPython
    & $RutaNssm set $NombreServicio AppParameters $argumentosUvicorn
    & $RutaNssm set $NombreServicio AppDirectory $rutaBackend
    & $RutaNssm set $NombreServicio DisplayName "SGAIE - Backend (FastAPI/Uvicorn)"
    & $RutaNssm set $NombreServicio Description "API del Sistema de Gestion de Arriendo de Infraestructura Electrica (CNEL EP)."
    & $RutaNssm set $NombreServicio Start SERVICE_AUTO_START
    & $RutaNssm set $NombreServicio AppStdout (Join-Path $rutaLogs "stdout.log")
    & $RutaNssm set $NombreServicio AppStderr (Join-Path $rutaLogs "stderr.log")
    & $RutaNssm set $NombreServicio AppRotateFiles 1
    & $RutaNssm set $NombreServicio AppRotateOnline 1
    & $RutaNssm set $NombreServicio AppRotateBytes 10485760
} else {
    Write-Host "==> El servicio '$NombreServicio' ya existe: se reiniciara para aplicar cambios." -ForegroundColor Cyan
}

Write-Host "==> Iniciando/reiniciando el servicio '$NombreServicio'..." -ForegroundColor Cyan
& $RutaNssm restart $NombreServicio

Write-Host ""
Write-Host "Instalacion completa. Verifique el estado con:" -ForegroundColor Green
Write-Host "    $RutaNssm status $NombreServicio"
Write-Host "Y la salud de la API con:" -ForegroundColor Green
Write-Host "    Invoke-WebRequest http://$HostBind`:$Puerto/api/v1/salud"
