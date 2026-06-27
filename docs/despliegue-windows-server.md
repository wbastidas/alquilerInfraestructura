# Despliegue de SGAIE en Windows Server

Esta guía describe cómo instalar SGAIE (Sistema de Gestión de Arriendo de
Infraestructura Eléctrica) en un Windows Server institucional de CNEL EP,
según los lineamientos de §3.3 de `ESPECIFICACION_TECNICA.md`: MariaDB como
servicio nativo de Windows, el backend FastAPI/Uvicorn como servicio de
Windows vía **NSSM**, y un reverse proxy (**IIS** o **Nginx para Windows**)
terminando HTTPS y sirviendo el frontend estático compilado.

## 1. Requisitos previos

| Componente | Versión / nota |
|---|---|
| Windows Server | 2019 o superior |
| Python | 3.12+, instalado para "todos los usuarios" y agregado al `PATH` |
| MariaDB | 11.x, instalado como servicio de Windows nativo |
| Node.js + pnpm | Node 20+ (para compilar el frontend); `corepack enable` habilita `pnpm` |
| NSSM | https://nssm.cc/ — descomprimir en una ruta fija, p. ej. `C:\nssm\nssm.exe` |
| IIS **o** Nginx para Windows | IIS con módulos **Application Request Routing (ARR)** y **URL Rewrite**, o el binario de Nginx para Windows |
| Certificado TLS | Emitido/gestionado por la institución, para terminar HTTPS en el reverse proxy |

> Todas las dependencias de Python del proyecto (`pyproject.toml`) son puras
> o usan ruedas precompiladas para Windows (no requieren toolchain de
> compilación nativa), cumpliendo el requisito de §3.3 de no depender de
> librerías que solo existan en Linux.

## 2. Preparar la base de datos (MariaDB)

1. Instalar MariaDB 11.x como servicio de Windows (instalador oficial).
2. Crear la base de datos y el usuario de la aplicación:

   ```sql
   CREATE DATABASE sgaie CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'sgaie'@'localhost' IDENTIFIED BY '<clave-fuerte>';
   GRANT ALL PRIVILEGES ON sgaie.* TO 'sgaie'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. Confirmar que el servicio de MariaDB está configurado con inicio
   `Automático` en `services.msc`.

## 3. Obtener el código

Clonar (o copiar) el repositorio en el servidor, por ejemplo en
`C:\SGAIE\alquilerInfraestructura`. Esta ruta es el valor por defecto que
usan los scripts de `infra\windows\`; si se usa otra ruta, pasarla con
`-RutaRepo` en cada script.

## 4. Instalar y arrancar el backend como servicio de Windows

Desde una consola de **PowerShell como Administrador**:

```powershell
cd C:\SGAIE\alquilerInfraestructura\infra\windows
.\instalar-backend.ps1 -RutaRepo "C:\SGAIE\alquilerInfraestructura" -RutaNssm "C:\nssm\nssm.exe"
```

El script (`infra/windows/instalar-backend.ps1`):

1. Crea el entorno virtual `backend\.venv` si no existe.
2. Instala las dependencias del backend (`pip install -e backend`).
3. Si no existe `backend\.env`, lo crea a partir de `backend\.env.example`
   — **el script se detiene aquí para que el administrador edite los
   secretos antes de continuar** (ver §5).
4. Aplica las migraciones de base de datos (`alembic upgrade head`).
5. Registra el servicio de Windows `SGAIE-Backend` con NSSM, ejecutando
   `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4`, con
   logs rotados en `backend\logs\stdout.log` / `stderr.log`.
6. Arranca (o reinicia, si ya existía) el servicio.

Para actualizaciones posteriores (`git pull` + nueva versión), volver a
ejecutar el mismo script: es idempotente y reinicia el servicio al final.

Verificar que el backend responde:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/salud
```

Para desinstalar el servicio (sin borrar código ni base de datos):

```powershell
.\desinstalar-backend.ps1 -RutaNssm "C:\nssm\nssm.exe"
```

## 5. Configurar y proteger `backend\.env`

Editar `backend\.env` (copiado desde `backend\.env.example`) con los valores
reales del entorno de producción:

- `DATABASE_URL`: cadena de conexión a la MariaDB del paso 2.
- `JWT_SECRET_KEY`: clave aleatoria de al menos 32 caracteres
  (recomendado ≥64). **No reutilizar la clave de desarrollo.**
- `AES_MASTER_KEY`: clave base64 de 32 bytes para el cifrado de campos
  sensibles (§4, columnas 🔒). Generar con:

  ```powershell
  python -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
  ```

- `CORS_ORIGENS`: el(los) dominio(s) HTTPS público(s) reales (nunca `*`).
- `LDAP_*`: datos del Active Directory institucional (ver
  `TODO: confirmar con cliente` en `app/auth/ldap_client.py` sobre el
  mapeo de OU/grupos — pendiente de confirmación con CNEL EP).

Tras editarlo, restringir los permisos del archivo para que solo la cuenta
de servicio y los administradores puedan leerlo:

```powershell
.\asegurar-env.ps1 -RutaEnv "C:\SGAIE\alquilerInfraestructura\backend\.env" -CuentaServicio "NT AUTHORITY\SYSTEM"
```

Por defecto NSSM ejecuta el servicio como `Local System`
(`NT AUTHORITY\SYSTEM`); si se configura una cuenta de servicio dedicada
con `nssm set SGAIE-Backend ObjectName ...`, pasar esa cuenta en
`-CuentaServicio`.

Después de cualquier cambio en `.env`, reiniciar el servicio:

```powershell
C:\nssm\nssm.exe restart SGAIE-Backend
```

## 6. Compilar y publicar el frontend

```powershell
.\publicar-frontend.ps1 -RutaRepo "C:\SGAIE\alquilerInfraestructura" -RutaWebroot "C:\inetpub\sgaie"
```

Esto ejecuta `pnpm install && pnpm build` en `frontend/` y copia el
contenido de `frontend\dist` al webroot que servirá IIS o Nginx.

Antes de compilar, asegurarse de que `frontend\.env` (o las variables de
entorno de build de Vite) apunten a la URL pública de la API, por ejemplo:

```
VITE_API_BASE_URL=https://sgaie.cnel.example.ec/api/v1
```

## 7. Reverse proxy + TLS

Elegir **una** de las dos opciones equivalentes en `infra/nginx-or-iis/`.
Ambas: sirven el frontend estático, reenvían `/api/*` al backend en
`127.0.0.1:8000`, fuerzan HTTPS y aplican el fallback de SPA (rutas de
React Router resueltas contra `index.html`).

### Opción A: IIS (`infra/nginx-or-iis/web.config`)

1. Instalar los módulos **Application Request Routing (ARR)** y
   **URL Rewrite** para IIS.
2. En *IIS Manager → (nivel de servidor) → Application Request Routing
   Cache → Server Proxy Settings*: habilitar **Enable proxy**.
3. Crear un sitio en IIS cuyo *Physical path* sea el webroot publicado en
   el paso 6 (p. ej. `C:\inetpub\sgaie`), con bindings HTTP (80, solo para
   redirección) y HTTPS (443, con el certificado institucional).
4. Copiar `infra/nginx-or-iis/web.config` a la raíz de ese webroot (ya
   queda junto a los archivos del build si se ejecuta el paso siguiente).
5. Reiniciar el sitio en IIS.

### Opción B: Nginx para Windows (`infra/nginx-or-iis/nginx.conf`)

1. Descomprimir el binario de Nginx para Windows (p. ej. en `C:\nginx`).
2. Copiar `infra/nginx-or-iis/nginx.conf` a `C:\nginx\conf\sgaie.conf` y
   ajustar `server_name`, `root` y las rutas de `ssl_certificate` /
   `ssl_certificate_key` a los valores reales del servidor.
3. Incluirlo desde `C:\nginx\conf\nginx.conf` (bloque `http { include
   conf/sgaie.conf; }`) o reemplazar directamente el `server` por defecto.
4. Ejecutar Nginx como servicio de Windows (NSSM, igual que el backend) o
   con el *Task Scheduler* en inicio del sistema.

## 8. Tareas programadas

La especificación (§3.3, §6.14, §7.2, §7.4) define tres jobs programados, todos
**idempotentes** (ejecutarlos más de una vez el mismo día no genera
duplicados):

| Job | Frecuencia (APScheduler) | Qué hace |
|---|---|---|
| Generación anual de alquileres | 1 de enero, 00:05 | Recorre las operadoras con contrato vigente y crea su `AlquilerAnual` del nuevo año (clonando `PostePorZona` del año anterior con montos en cero), genera una `Alerta` de facturación pendiente y un registro en `LogAuditoria`. |
| Detección de morosidad | Diario, 01:00 | Marca como `VENCIDA` las facturas cuya fecha de vencimiento ya pasó y genera la `Alerta` de morosidad correspondiente (§7.4). |
| Detección de vencimientos próximos | Diario, 02:00 | Genera una `Alerta` de vencimiento de contrato, póliza de garantía o título habilitante cuando la fecha real cae dentro de la ventana de anticipación configurada (`dias_anticipacion_alerta_vencimiento`, §6.14). |

Dos formas de ejecutarlos, ambas ya implementadas en este repositorio:

1. **In-process con APScheduler (predeterminado)**: `app/jobs/scheduler.py`
   registra un `BackgroundScheduler` que arranca junto con el backend (evento
   `startup` de FastAPI, ver `app/main.py`) y dispara los tres jobs en los
   horarios de la tabla anterior (zona horaria `America/Guayaquil`). No
   requiere configuración adicional: funciona mientras el servicio NSSM del
   backend esté corriendo.
2. **Respaldo vía Programador de tareas de Windows**: si el backend no corre
   24/7 (p. ej. se reinicia por mantenimiento justo cuando debía disparar
   alguno de los jobs), programar tareas equivalentes que ejecuten:

   ```powershell
   C:\sgaie\backend\venv\Scripts\python.exe -m app.jobs.cli_generacion_anual
   C:\sgaie\backend\venv\Scripts\python.exe -m app.jobs.cli_morosidad
   C:\sgaie\backend\venv\Scripts\python.exe -m app.jobs.cli_vencimientos
   ```

   con disparadores: anual el 1 de enero para `cli_generacion_anual`, y
   diario para `cli_morosidad` y `cli_vencimientos`. Al ser idempotentes,
   ejecutar ambos mecanismos (in-process y Task Scheduler) el mismo día no
   genera duplicados.

## 9. Verificación post-instalación

- `Invoke-WebRequest https://sgaie.cnel.example.ec/api/v1/salud` → `200 OK`.
- Cargar `https://sgaie.cnel.example.ec/` en un navegador → pantalla de
  login del frontend.
- Iniciar sesión con un usuario local de prueba y confirmar que el panel,
  el listado de operadoras y el de contratos cargan datos desde la API
  (sin errores de CORS ni 401/403 inesperados en la consola del navegador).
- Revisar `backend\logs\stdout.log` / `stderr.log` para confirmar que
  Uvicorn arrancó sin excepciones.

## 10. Resumen de scripts y configuraciones

| Archivo | Propósito |
|---|---|
| `infra/windows/instalar-backend.ps1` | Instala dependencias, migra la BD y registra/arranca el servicio `SGAIE-Backend` (NSSM). |
| `infra/windows/desinstalar-backend.ps1` | Detiene y elimina el servicio de Windows del backend. |
| `infra/windows/asegurar-env.ps1` | Restringe permisos NTFS de `backend\.env` a Administradores y la cuenta de servicio. |
| `infra/windows/publicar-frontend.ps1` | Compila el frontend (`pnpm build`) y publica `dist/` en el webroot del reverse proxy. |
| `infra/nginx-or-iis/web.config` | Reverse proxy + TLS + SPA fallback con IIS (ARR + URL Rewrite). |
| `infra/nginx-or-iis/nginx.conf` | Alternativa equivalente con Nginx para Windows. |
