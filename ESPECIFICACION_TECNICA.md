# Especificación Técnica — Sistema de Gestión de Arriendo de Infraestructura Eléctrica (SGAIE)

> Documento de especificaciones para desarrollo con **Claude Code**.

> Versión 1.0 · Cliente: CNEL EP (Matriz + Unidades de Negocio) · Dominio: arrendamiento de postes/ductos a operadoras de telecomunicaciones.

---

## 0. Cómo usar este documento (instrucciones para Claude Code)

Este archivo es la fuente de verdad del proyecto. Al iniciar el desarrollo:

1. Lee este documento completo antes de generar código.
2. Crea el **monorepo** con la estructura de la sección 12.
3. Implementa primero el núcleo: modelo de datos (§6), autenticación y roles (§5), seguridad transversal (§4). Sin estos, ningún módulo es válido.
4. Implementa los módulos (§7) en el orden de fases de la sección 13.
5. Cada entidad debe tener migración (Alembic), modelo (SQLAlchemy), esquema (Pydantic), servicio, router y pruebas.
6. No inventes campos ni reglas que no estén aquí; si algo es ambiguo, déjalo marcado con `# TODO: confirmar con cliente` y un valor por defecto razonable.
7. Todo el código, comentarios, nombres de variables y mensajes de UI en **español**.

---

## 1. Objetivo

Aplicación **web multiplataforma** y **segura** para gestionar el ciclo completo del arrendamiento de infraestructura eléctrica (postes y ductos) de CNEL EP a operadoras de telecomunicaciones ("proveedores" / "arrendatarias"). Cubre: registro de empresas y contratos, control anual de postes y recaudación, portal público de solicitudes, gestión de pagos, flujo de autorizaciones multinivel, registro de novedades en campo y generación de documentos oficiales (solicitud, informe de factibilidad, contrato, ampliación).

El sistema debe poder **instalarse en un servidor Windows Server** de la institución.

---

## 2. Glosario y actores

| Término | Definición |
|---|---|
| **Matriz** | Nivel corporativo de CNEL EP. Acceso de **solo lectura/consulta** consolidada de todas las Unidades de Negocio. |
| **Unidad de Negocio (UN)** | Empresa eléctrica regional. Acceso de **edición** sobre los datos de su propia UN. |
| **Arrendadora** | CNEL EP (propietaria de los postes). |
| **Arrendataria / Proveedor** | Operadora de telecomunicaciones que arrienda los postes. |
| **CableOperadora** | Entidad que modela a la empresa proveedora/arrendataria dentro del sistema. |
| **Administrador de Contrato** | Funcionario CNEL EP que gestiona un contrato vigente. |
| **Delegado Coordinador** | Recibe solicitudes de proveedores **sin** contrato. |
| **Delegado Técnico** | Realiza la revisión técnica y el informe de factibilidad. |
| **Canon** | Valor anual de arrendamiento por poste. |
| **SIG / GIS** | Información geoespacial (File Geodatabase ArcGIS, WGS84 / UTM 17S). |
| **MAPOD** | Manual para el Arrendamiento y Uso de Infraestructura de Postes y Ductos. |

### 2.1 Roles del sistema

| Rol | Ámbito | Permisos |
|---|---|---|
| `MATRIZ_CONSULTA` | Global | Solo lectura de todo (dashboards, reportes consolidados). |
| `UN_ADMIN` | Su UN | Lectura/escritura total dentro de su UN. |
| `UN_ADMIN_CONTRATO` | Su UN | Gestiona contratos asignados, autoriza ampliaciones. |
| `UN_DELEGADO_COORDINADOR` | Su UN | Recibe y deriva solicitudes de proveedores sin contrato. |
| `UN_DELEGADO_TECNICO` | Su UN | Revisión técnica, informe de factibilidad, registro de novedades. |
| `UN_GERENTE` | Su UN | Aprobación gerencial. |
| `UN_JURIDICO` | Su UN | Genera/valida contrato a partir del modelo base. |
| `PROVEEDOR` | Su empresa | Portal externo: crea solicitudes, sube documentos, ve estado. |
| `SUPERADMIN` | Global | Configuración, catálogos, parámetros, gestión de usuarios. |

> El detalle fino de permisos por endpoint se define con un sistema RBAC (sección 5.3). La regla rectora es: **Matriz lee; UN edita lo suyo; Proveedor solo su propio expediente.**

---

## 3. Arquitectura general

### 3.1 Principios

- **Monorepositorio** que contiene backend, frontend, infraestructura y documentación.
- **Multiplataforma**: el frontend corre en cualquier navegador moderno; el backend y la BD se despliegan en **Windows Server** (y deben ser portables a Linux para desarrollo).
- **Frontend sencillo de entender**: stack estándar, sin abstracciones exóticas.
- Separación estricta cliente/servidor vía **API REST** documentada (OpenAPI).

### 3.2 Stack tecnológico

**Backend**
- Lenguaje: **Python 3.12+**
- Framework: **FastAPI** (async, validación, OpenAPI automático)
- Servidor ASGI: **Uvicorn** (con `--workers`) detrás de reverse proxy
- ORM: **SQLAlchemy 2.0** (estilo declarativo tipado)
- Migraciones: **Alembic**
- Validación/serialización: **Pydantic v2**
- Tareas programadas: **APScheduler** (in-process) con respaldo documentado vía Windows Task Scheduler
- Base de datos: **MariaDB 11.x** (driver `mariadb` o `PyMySQL`)
- Generación de documentos: **python-docx** (a partir de plantillas `.dotx`/`.docx`) y opción a PDF
- Autenticación dominio Windows: **ldap3** (LDAP/Active Directory)
- Tests: **pytest** + **httpx** + base de datos de prueba

**Frontend**
- **React 18 + TypeScript**
- Bundler: **Vite**
- Enrutamiento: **React Router**
- Datos/servidor-estado: **TanStack Query** (React Query)
- Formularios + validación: **React Hook Form + Zod**
- UI: librería de componentes consistente y sobria (**Mantine** o **shadcn/ui** + Tailwind). Elegir una sola y mantenerla.
- Mapas (para SIG/novedades georreferenciadas): **Leaflet** (`react-leaflet`)
- Cliente HTTP: **axios** con interceptores para JWT/refresh

**Monorepo / tooling**
- Gestor JS: **pnpm** con workspaces
- Orquestación de tareas: scripts `pnpm` simples (o **Turborepo** si se justifica, sin sobre-ingeniería)
- Calidad: **ruff + black + mypy** (Python), **eslint + prettier** (TS)
- Contenedores para desarrollo: **Docker Compose** (MariaDB + backend + frontend)

### 3.3 Despliegue en Windows Server

El despliegue objetivo es **Windows Server** institucional:

- **MariaDB**: instalación nativa como servicio de Windows.
- **Backend FastAPI/Uvicorn**: ejecutarse como **servicio de Windows** mediante **NSSM** (Non-Sucking Service Manager) o `pywin32`. Documentar el `.bat`/script de arranque.
- **Reverse proxy / TLS**: **IIS** con módulo de reverse proxy (ARR + URL Rewrite) o **Nginx para Windows**, terminando **HTTPS** y sirviendo el frontend estático compilado (`/dist`).
- **Tareas programadas**: APScheduler dentro del proceso; alternativamente un comando CLI (`python -m app.jobs generar_anios`) disparado por el **Programador de tareas de Windows** cada 1 de enero.
- Variables de entorno y secretos en archivo `.env` protegido por ACL de Windows (no en el repo).
- Entregar un **script de instalación** documentado (PowerShell) y un `README` de despliegue.

> Requisito: la aplicación debe funcionar **sin dependencias que solo existan en Linux**. Evitar librerías que requieran compilación nativa problemática en Windows.

---

## 4. Requisitos de seguridad (transversales, obligatorios)

Estos controles son **no negociables** y aplican a todo el sistema:

1. **Autenticación OAuth 2.0 + JWT con refresh tokens.**
   - Access token de vida corta (p. ej. 15 min) + refresh token de vida larga (p. ej. 7 días) almacenado de forma segura (cookie `HttpOnly`, `Secure`, `SameSite=Strict`).
   - Rotación de refresh tokens y revocación (lista negra en BD/cache).
2. **Doble vía de inicio de sesión** (ver §5):
   - **Dominio Windows** (LDAP/Active Directory) para funcionarios CNEL EP.
   - **Usuario y clave** gestionado por el sistema (proveedores y cuentas locales), con hashing **bcrypt/argon2**.
3. **Rate limiting por IP y por usuario** en endpoints sensibles (login, portal público, subida de archivos). Implementar con middleware (p. ej. `slowapi`) y almacenamiento en cache.
4. **Encriptación AES-256** para datos sensibles en reposo (campos como cédula, RUC del representante, datos de contacto personales, credenciales de pasarela). Usar una clave maestra desde variable de entorno; cifrado a nivel de aplicación para columnas marcadas como sensibles.
5. **CORS** configurado de forma restrictiva: orígenes permitidos explícitos por entorno, no `*` en producción.
6. **Validación de inputs contra SQL injection y XSS**:
   - SQLi: uso exclusivo del ORM con consultas parametrizadas; prohibido SQL concatenado.
   - XSS: sanitización/escape de toda entrada que se renderice; cabeceras de seguridad (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`).
   - Validación estricta de tipos y tamaños con Pydantic/Zod en ambos extremos.
7. **Logging de auditoría completo**: registrar quién, qué, cuándo y desde dónde para toda operación de creación/modificación/eliminación y para accesos a datos sensibles (ver entidad `LogAuditoria`, §6).
8. **Subida de archivos segura**: validar tipo MIME y extensión (zip de SIG, PDF, imágenes), límite de tamaño, almacenamiento fuera del webroot, nombres saneados, análisis antivirus si está disponible.
9. **HTTPS obligatorio** en producción; redirección de HTTP a HTTPS.
10. **Principio de mínimo privilegio** en BD y en roles de aplicación.

---

## 5. Autenticación, autorización y modelo Matriz/UN

### 5.1 Doble vía de autenticación

| Vía | Usuarios | Mecanismo |
|---|---|---|
| **Dominio Windows (LDAP/AD)** | Funcionarios CNEL EP (Matriz y UN) | Bind LDAP contra Active Directory con `ldap3`. Tras autenticar, se mapea el usuario AD a un usuario interno con su rol y UN. |
| **Usuario y clave local** | Proveedores (portal externo) y cuentas de respaldo | Credenciales propias, hash argon2/bcrypt, verificación de correo. |

La pantalla de login ofrece ambas opciones. El backend emite el mismo par de tokens JWT en ambos casos; el `claim` del token incluye: `sub` (usuario), `rol`, `unidad_negocio_id` (o `null` para Matriz/Superadmin), `tipo_cuenta` (`AD` | `LOCAL` | `PROVEEDOR`).

### 5.2 Modelo Matriz vs. Unidad de Negocio

- **Matriz** (`MATRIZ_CONSULTA`): sin `unidad_negocio_id`. Acceso de **solo lectura** a datos consolidados de **todas** las UN. Nunca puede crear, editar ni borrar registros operativos.
- **Unidad de Negocio** (`UN_*`): con `unidad_negocio_id`. Puede **leer y editar** únicamente los registros cuyo `unidad_negocio_id` coincida con el suyo.
- Toda consulta operativa debe filtrarse automáticamente por la UN del usuario (salvo Matriz/Superadmin). Implementar como **filtro de seguridad a nivel de servicio/repositorio** (no solo en la UI).

### 5.3 Autorización (RBAC)

- Tabla de roles y permisos (`rol`, `permiso`, `rol_permiso`).
- Decorador/dependencia de FastAPI que valida rol + ámbito (UN) en cada endpoint.
- Regla de oro reforzada en backend: **Matriz = read-only global; UN = read-write de su UN; Proveedor = read-write de su propio expediente.**

---

## 6. Modelo de datos

Notación: PK = clave primaria, FK = clave foránea. Todas las entidades incluyen `id`, `creado_en`, `actualizado_en`, `creado_por`, `actualizado_por`. Los campos marcados 🔒 se almacenan **cifrados (AES-256)**.

### 6.1 `UnidadNegocio`
- `id` (PK)
- `codigo` (único, p. ej. "UN-GUAYAS")
- `nombre`
- `provincia`
- `activo` (bool)

### 6.2 `Usuario`
- `id` (PK)
- `username` (único)
- `nombre_completo`
- `correo`
- `tipo_cuenta` (enum: `AD`, `LOCAL`, `PROVEEDOR`)
- `password_hash` (nullable; solo `LOCAL`/`PROVEEDOR`)
- `rol_id` (FK → Rol)
- `unidad_negocio_id` (FK → UnidadNegocio, nullable para Matriz/Superadmin)
- `cable_operadora_id` (FK → CableOperadora, nullable; solo para `PROVEEDOR`)
- `activo` (bool)
- `ultimo_acceso`

### 6.3 `Rol` / `Permiso` / `RolPermiso`
- `Rol`: `id`, `codigo`, `nombre`, `descripcion`
- `Permiso`: `id`, `codigo`, `descripcion`
- `RolPermiso`: `rol_id`, `permiso_id`

### 6.4 `CableOperadora` (empresa proveedora / arrendataria)
- `id` (PK)
- `numero_registro` (único)
- `nombre_empresa`
- `nombres_comerciales` (lista / tabla hija `NombreComercial`)
- `ruc` 🔒
- `cuenta_contrato`
- `representante_legal`
- `representante_cedula` 🔒
- `titulo_habilitante_numero`
- `titulo_habilitante_vigencia`
- `arcotel_resolucion`
- `servicios_autorizados` (texto)
- `cobertura_geografica` (enum: `NACIONAL`, `REGIONAL`, `LOCAL`)
- `telefonos` (tabla hija `TelefonoOperadora`: `id`, `cable_operadora_id`, `numero`, `tipo`)
- `correo`
- `estado_contrato` (enum: `ACTIVO`, `CADUCADO`, `SUSPENDIDO`, `EN_RENOVACION`, `EN_JURIDICO`)
- `fecha_firma_contrato`
- `fecha_caducidad`
- `administrador_contrato` (texto o FK → Usuario)
- `tipo_contrato` (enum: `NACIONAL`, `REGIONAL`, `LOCAL`)
- `unidad_negocio_id` (FK)

**Tabla hija `ResponsableTecnicoZona`** (responsables técnicos por zonas):
- `id` (PK)
- `cable_operadora_id` (FK)
- `nombre`
- `cedula` 🔒
- `cargo` (enum/texto: Administrativo, Técnico, Coordinador de Campo, etc.)
- `telefono`
- `correo`
- `zona_cobertura` (provincia/cantón/zona)

### 6.5 `Contrato`
Registra el contrato generado como producto del flujo de autorización.
- `id` (PK)
- `cable_operadora_id` (FK)
- `unidad_negocio_id` (FK)
- `numero_contrato` (único)
- `tipo_cobertura` (enum: `NACIONAL`, `REGIONAL`, `LOCAL`)
- `fecha_suscripcion`
- `fecha_inicio`
- `fecha_fin` (vigencia 2 años, renovable una vez — ver cláusula 8 del modelo)
- `estado` (enum: `VIGENTE`, `EN_RENOVACION`, `TERMINADO`, `SUSPENDIDO`, `EN_JURIDICO`)
- `total_postes`
- `total_ductos_m`
- `canon_anual_total`
- `poliza_numero`
- `poliza_aseguradora`
- `poliza_valor`
- `poliza_vigencia_inicio`
- `poliza_vigencia_fin`
- `archivo_contrato_id` (FK → Documento)
- `solicitud_id` (FK → Solicitud, origen)
- `informe_factibilidad_id` (FK → InformeFactibilidad)

### 6.6 `AlquilerAnual`
Control anual dinámico por contrato/operadora.
- `id` (PK)
- `cable_operadora_id` (FK)
- `contrato_id` (FK, nullable)
- `unidad_negocio_id` (FK)
- `anio` (int)
- `postes_sig` (cantidad en sistema SIG)
- `postes_fisicos` (cantidad real verificada en campo)
- `monto_facturado` (decimal)
- `monto_recaudado` (decimal)
- `monto_pendiente_recaudar` (decimal, derivado: facturado − recaudado)
- `fecha_facturacion`
- `estado_pago` (enum: `PENDIENTE`, `PARCIAL`, `COMPLETO`)
- `observaciones`
- `poliza_garantia_fecha`
- `poliza_garantia_archivo_id` (FK → Documento)
- Restricción única: (`cable_operadora_id`, `anio`).

**Tabla hija `PostePorZona`** (detalle de postes por zona geográfica — distintos cantones/parroquias con distintas cantidades):
- `id` (PK)
- `alquiler_anual_id` (FK)
- `provincia`
- `canton`
- `parroquia` (nullable)
- `tipo_zona` (enum: `CAPITAL_PROVINCIAL`, `CABECERA_CANTONAL`, `OTRO_SECTOR`) → determina el canon
- `cantidad_postes`
- `cantidad_ductos_m`
- `canon_unitario` (decimal; valor vigente del catálogo, ver §6.12)
- `subtotal` (derivado: cantidad × canon_unitario)

> **Auto-generación anual**: cada **1 de enero**, un job programado crea automáticamente un registro `AlquilerAnual` del nuevo año para cada operadora con contrato vigente, copiando como base la estructura de `PostePorZona` del año anterior (montos en cero, estado `PENDIENTE`). Ver §7.2.

### 6.7 `Solicitud`
Solicitudes desde el portal externo (nueva o ampliación).
- `id` (PK)
- `numero_referencia` (único, para seguimiento)
- `tipo` (enum: `NUEVO_CONTRATO`, `AMPLIACION`)
- `cable_operadora_id` (FK; para nuevos, se crea/asocia al registrarse)
- `contrato_id` (FK, nullable; solo ampliaciones)
- `unidad_negocio_id` (FK; según cobertura)
- `dirigida_a` (enum: `GERENTE_GENERAL`, `ADMIN_UNIDAD_NEGOCIO`, `ADMIN_CONTRATO`)
- `cobertura` (enum: `NACIONAL`, `REGIONAL`, `LOCAL`)
- `provincias_involucradas` (texto/tabla hija)
- `postes_solicitados`
- `ductos_solicitados_m`
- `objetivo_proyecto` (texto)
- `tipo_redes` (texto: Fibra Óptica / Coaxial / Otros)
- `cronograma_inicio`, `cronograma_fin`, `puesta_en_servicio`
- `estado` (enum del workflow, ver §8)
- `fecha_creacion`
- Tablas hijas: `RutaPropuesta` (provincia/ciudad/recinto, rutas, postes usados, nuevos, totales), `ContactoSolicitud` (representante legal, responsable técnico, coordinador de campo, contratista).

### 6.8 `Documento`
Archivos cargados/generados (SIG zip, PDFs, imágenes, contrato, etc.).
- `id` (PK)
- `entidad_tipo` (enum: `SOLICITUD`, `CONTRATO`, `ALQUILER`, `NOVEDAD`, `OPERADORA`, `PAGO`)
- `entidad_id`
- `tipo_documento` (enum del checklist §11: `SOLICITUD_FORMAL`, `TITULO_HABILITANTE`, `DOC_SOCIETARIA`, `RUC`, `CEDULA_REP_LEGAL`, `COMPROBANTE_PAGO_ENERGIA`, `POLIZA`, `PLAN_EXPANSION`, `SIG_GEODATABASE`, `ESPEC_TECNICAS`, `LISTADO_CONTACTOS`, `CONTRATO_FIRMADO`, `INFORME_FACTIBILIDAD`, `FOTO_PLACAS`, `OTRO`)
- `nombre_archivo`
- `ruta_almacenamiento`
- `mime_type`
- `tamano_bytes`
- `hash_sha256` (integridad)
- `estado_validacion` (enum: `PENDIENTE`, `VALIDADO`, `OBSERVADO`, `RECHAZADO`)
- `observacion_validacion`

### 6.9 `InformeFactibilidad`
- `id` (PK)
- `solicitud_id` (FK)
- `cable_operadora_id` (FK)
- `unidad_negocio_id` (FK)
- `codigo_oficio`
- `fecha`
- `cobertura` (enum)
- `ubicaciones` (tabla hija: provincia, cantones, UN)
- `postes_solicitados`, `postes_viables`, `postes_no_viables`
- `ductos_solicitados_m`, `ductos_viables_m`, `ductos_no_viables_m`
- `porcentaje_factibilidad`
- `revision_documental_estado`, `fecha_ultima_subsanacion`
- `sig_validado` (bool), `sig_validador`, `sig_fecha_validacion`
- `inspeccion_fecha_inicio`, `inspeccion_fecha_fin`, `rutas_verificadas`, `personal_participante`
- `conclusiones` (texto)
- `archivo_id` (FK → Documento, el informe generado)

### 6.10 `Autorizacion` (paso del workflow)
- `id` (PK)
- `solicitud_id` (FK)
- `etapa` (enum: `RECEPCION`, `REVISION_TECNICA`, `APROBACION_GERENCIAL`, `REVISION_JURIDICA`, `AUTORIZACION_FINAL`)
- `responsable_id` (FK → Usuario)
- `estado` (enum: `PENDIENTE`, `APROBADO`, `RECHAZADO`, `OBSERVADO`)
- `comentario`
- `fecha`
- Tabla hija `AdjuntoAutorizacion` (FK → Documento).

### 6.11 `Pago` / `Factura`

**`Factura`**
- `id` (PK)
- `cable_operadora_id` (FK)
- `contrato_id` (FK)
- `alquiler_anual_id` (FK)
- `numero_factura`
- `fecha_emision`
- `fecha_vencimiento`
- `monto`
- `iva`
- `total`
- `estado` (enum: `EMITIDA`, `PAGADA`, `VENCIDA`, `PARCIAL`, `ANULADA`)
- `archivo_xml_id`, `archivo_pdf_id` (factura electrónica)

**`Pago`**
- `id` (PK)
- `factura_id` (FK)
- `cable_operadora_id` (FK)
- `monto`
- `tipo` (enum: `PARCIAL`, `TOTAL`)
- `metodo` (enum: `TRANSFERENCIA`, `DEPOSITO`, `CHEQUE`, `TARJETA`, `VENTANILLA`, `PASARELA`)
- `referencia_transaccion` 🔒
- `fecha_pago`
- `conciliado` (bool)
- `fecha_conciliacion`

### 6.12 `CatalogoCanon` (parametrizable)
Valores del canon por tipo de zona, versionables (pueden actualizarse por directriz ministerial — ver cláusula 1.11 / 6.1.3 del modelo).
- `id` (PK)
- `tipo_zona` (enum: `CAPITAL_PROVINCIAL`, `CABECERA_CANTONAL`, `OTRO_SECTOR`)
- `valor` (decimal)
- `vigente_desde`, `vigente_hasta`
- `referencia_normativa` (oficio/resolución)

Valores semilla por defecto (Oficio MEER-SDCE-2016-0181-OF, **actualizables**):

| Tipo de zona | Canon anual (USD) |
|---|---|
| Capital de provincia | 9.00 |
| Cabecera cantonal | 7.02 |
| Otros sectores | 6.03 |

### 6.13 `Novedad`
- `id` (PK)
- `cable_operadora_id` (FK)
- `contrato_id` (FK, nullable)
- `unidad_negocio_id` (FK)
- `tipo` (enum: `INSPECCION_PROGRAMADA`, `DANO_REPORTADO`, `MANTENIMIENTO`)
- `descripcion`
- `fecha_programada`, `fecha_ejecucion`
- `estado` (enum: `PROGRAMADA`, `EN_PROCESO`, `EJECUTADA`, `CERRADA`)
- `latitud`, `longitud` (geolocalización)
- `ficha_informe_id` (FK → Documento; ficha de informe de mantenimiento)
- Tabla hija `FotografiaNovedad` (FK → Documento, con coordenadas).

### 6.14 `Alerta`
Vencimientos (contrato, póliza, pago, título habilitante).
- `id` (PK)
- `tipo` (enum: `VENCIMIENTO_CONTRATO`, `VENCIMIENTO_POLIZA`, `MOROSIDAD`, `VENCIMIENTO_TITULO`, `SIG_ANUAL_PENDIENTE`)
- `entidad_tipo`, `entidad_id`
- `unidad_negocio_id` (FK)
- `mensaje`
- `severidad` (enum: `INFO`, `ADVERTENCIA`, `CRITICA`)
- `fecha_generacion`
- `leida` (bool)

### 6.15 `LogAuditoria`
- `id` (PK)
- `usuario_id` (FK)
- `accion` (enum: `CREAR`, `EDITAR`, `ELIMINAR`, `LOGIN`, `LOGOUT`, `DESCARGA`, `ACCESO_DATO_SENSIBLE`)
- `entidad_tipo`, `entidad_id`
- `descripcion`
- `valores_antes` (JSON), `valores_despues` (JSON)
- `ip_origen`
- `user_agent`
- `fecha`

---

## 7. Módulos funcionales

### 7.1 Módulo 1 — Gestión de Empresas y Contratos

CRUD completo de `CableOperadora` y `Contrato` con todos los campos de §6.4–§6.5.

Funcionalidades:
- Alta/edición/consulta de operadoras con sus teléfonos, nombres comerciales y responsables técnicos por zona.
- Estados de contrato con transiciones controladas: `ACTIVO → EN_RENOVACION → ACTIVO/CADUCADO`, `ACTIVO → SUSPENDIDO`, `ACTIVO → EN_JURIDICO`.
- Vista de detalle del expediente completo de cada operadora (datos, contratos, alquileres anuales, pagos, solicitudes, novedades, documentos).
- Búsqueda y filtros: por estado, tipo de contrato, UN, fecha de caducidad, morosidad.
- **Matriz**: vista consolidada de todas las operadoras de todas las UN (solo lectura).
- Generación del documento de **contrato** a partir del modelo base (§9.1).

### 7.2 Módulo 2 — Gestión de Postes y Alquileres

Maneja `AlquilerAnual` + `PostePorZona`.

Funcionalidades:
- Registro y edición de cantidades de postes por año, **desglosado por provincia/cantón/parroquia** y tipo de zona (que determina el canon aplicable).
- Comparación `postes_sig` vs. `postes_fisicos` con alerta de discrepancia.
- Cálculo automático del canon anual: suma de (`cantidad_postes` × `canon_unitario`) por zona, tomando el valor vigente de `CatalogoCanon`.
- Seguimiento de montos facturado / recaudado / pendiente y `estado_pago`.
- Registro de póliza de garantía anual (fecha + archivo).
- **Auto-generación de registros para nuevos años**: job programado el **1 de enero** (APScheduler / Windows Task Scheduler) que:
  1. Recorre operadoras con contrato vigente.
  2. Crea su `AlquilerAnual` del nuevo año.
  3. Clona la estructura de `PostePorZona` del año anterior con montos en cero y `estado_pago = PENDIENTE`.
  4. Genera alerta de "facturación pendiente del nuevo período".
  - El job debe ser **idempotente** (no duplicar si ya existe el año) y registrarse en `LogAuditoria`.

### 7.3 Módulo 3 — Portal de Solicitudes Externas (público)

Portal separado para proveedores (`PROVEEDOR`), con su propia UI y registro de cuenta.

Funcionalidades:
- **Registro y creación de cuenta** del proveedor (correo verificado, datos de empresa → crea `CableOperadora` en estado preliminar).
- **Solicitar nuevo arrendamiento** según el formato establecido (§9.2): formulario que captura alcance, rutas propuestas, información del proyecto, contactos y compromisos. Genera `Solicitud` tipo `NUEVO_CONTRATO`.
- **Solicitar ampliación** de postes de un contrato existente (§9.4): genera `Solicitud` tipo `AMPLIACION`.
- **Carga de documentación requerida**: base SIG en `.zip`, PDFs y otros archivos, validados según el checklist de §11. Cada archivo → `Documento` con su `tipo_documento`.
- **Seguimiento de estado** de sus solicitudes (timeline del workflow §8) por `numero_referencia`.
- **Notificaciones** de aceptación/observación/rechazo (correo + en la plataforma).
- Al aprobarse y firmarse, **registrar el contrato** resultante (`Contrato`) y enlazarlo a la solicitud.

Reglas de enrutamiento de la solicitud (según modelo):
- Cobertura **regional o nacional** → dirigida al **Gerente General** / Delegado Coordinador.
- Cobertura **local** → dirigida al **Administrador de Unidad de Negocio**.
- Si el proveedor **ya tiene contrato** (ampliación) → dirigida al **Administrador de Contrato**.

### 7.4 Módulo 4 — Gestión de Pagos

Funcionalidades:
- Registro de **pagos parciales y totales** contra facturas (`Pago` ↔ `Factura`).
- Registro de **facturas electrónicas** (carga de XML + PDF).
- **Integración con pasarela de pagos** (diseñar con interfaz/adaptador desacoplado; dejar `# TODO: confirmar proveedor de pasarela`).
- **Conciliación bancaria**: marcar pagos como conciliados, cruce con estados de cuenta.
- **Reportes de morosidad** (operadoras con `monto_pendiente_recaudar > 0` y facturas vencidas).
- **Alertas de vencimiento** de facturas (genera `Alerta` tipo `MOROSIDAD`).
- Cálculo de **intereses por mora** a tasa activa referencial del BCE (parametrizable) según cláusula 6.1.6 del modelo.

### 7.5 Módulo 5 — Sistema de Autorizaciones (workflow multinivel)

Motor de aprobación que mueve cada `Solicitud` por etapas (ver diagrama §8). En cada etapa:
- Asignación al responsable del rol correspondiente.
- Acciones: aprobar, observar (devolver para subsanación), rechazar.
- **Comentarios y adjuntos** en cada paso (`Autorizacion` + `AdjuntoAutorizacion`).
- **Notificaciones** automáticas en cada cambio de etapa.
- **Historial completo** e inmutable de autorizaciones (consultable como timeline).
- Al llegar a `AUTORIZACION_FINAL`: generar **documento firmado** para el proveedor y crear/activar el `Contrato`.

### 7.6 Módulo 6 — Registro de Novedades

Funcionalidades:
- **Inspecciones programadas**: agenda, asignación a delegado técnico, resultado.
- **Daños reportados**: registro con descripción, gravedad, responsable.
- **Mantenimientos realizados**: con **ficha de informe** adjunta.
- **Fotografías y geolocalización**: subida de fotos con coordenadas; visualización en **mapa (Leaflet)**.
- Filtros por tipo, estado, fecha, operadora, UN.

---

## 8. Workflow de autorizaciones (detalle)

Estados de `Solicitud` y transiciones:

```
[BORRADOR]
   │  (proveedor envía)
   ▼
[RECEPCION]  ── recibe: Delegado Coordinador (sin contrato) / Administrador (con contrato)
   │  aprueba/deriva
   ▼
[REVISION_TECNICA]  ── Delegado Técnico: valida documentación + SIG + inspección de campo
   │  genera InformeFactibilidad (favorable)
   ▼
[APROBACION_GERENCIAL]  ── Gerente UN/General: con informe favorable
   │  (si es NUEVO contrato) ▼
[REVISION_JURIDICA]  ── Jurídico: elabora contrato desde el modelo base
   │
   ▼
[AUTORIZACION_FINAL]  ── documento firmado emitido al proveedor → se registra Contrato
   │
   ▼
[FINALIZADA]
   ├─► en cualquier etapa: [OBSERVADA] (vuelve al proveedor para subsanar)
   └─► en cualquier etapa: [RECHAZADA] (fin)
```

- Para **ampliaciones** (proveedor con contrato), el flujo puede omitir `REVISION_JURIDICA` y resolver con un **Certificado de Autorización de Incremento/Reducción de Postes** (cláusula 5.2 del modelo: atención en término máximo de 20 días, sin modificar el contrato).
- Cada transición se registra con responsable, fecha, comentario y adjuntos, y dispara notificación.
- Plazos máximos configurables por etapa para alimentar alertas de SLA.

---

## 9. Plantillas documentales (generación automática)

El sistema debe **generar documentos** rellenando plantillas con datos del expediente, usando `python-docx` sobre archivos plantilla `.docx`/`.dotx` (membretados). Las plantillas se guardan en `infra/plantillas/` y se mapean los campos `[PLACEHOLDER]` a datos del sistema. Cada plantilla genera un `Documento` asociado.

### 9.1 Contrato de arrendamiento (modelo base CNEL EP)

Documento extenso de 23 cláusulas (ANTECEDENTES, DOCUMENTOS HABILITANTES, OBJETO, CONDICIONES Y OBLIGACIONES, CANON Y FORMA DE PAGO, PÓLIZA, PLAZO, PROHIBICIONES, ADMINISTRACIÓN, TERMINACIÓN, etc.).

Campos a parametrizar (entre otros): arrendadora (UN/representante), arrendataria (razón social/representante/calidad), antecedentes (oficios, fechas, resoluciones), tabla de canon por zona con cantidades y subtotales, forma de pago, datos de póliza (No., aseguradora, valor = 20% del contrato, mínimo USD 10.000), plazo (2 años renovable una vez), administradores de contrato (CNEL y compañía con correo/teléfono), domicilio electrónico para notificaciones, autorización de tratamiento de datos personales (LOPDP), firmas.

Reglas de negocio embebidas en el contrato que el sistema debe respetar/parametrizar:
- Canon por zona (capital provincial / cabecera cantonal / otros) desde `CatalogoCanon`.
- Forma de pago: anual/semestral/mensual, vencimiento factura 30 días.
- Cada poste pagado permite máx. 2 cables de transporte + 8 de abonado + 1 elemento de red.
- Póliza = 20% del valor total del contrato, mínimo USD 10.000; reajuste si aumento de postes/precio > 50%.
- Plazo 2 años, renovable por igual período una sola vez (aviso 30 días).
- Mora: intereses a tasa activa referencial BCE; falta de pago > 3 meses = causal de terminación; retiro de redes por falta de pago > 60 días.
- Planimetría SIG actualizada dentro del primer trimestre de cada año.

### 9.2 Solicitud de suscripción de contrato (Anexo 2)

Plantilla con: fecha/ciudad, destinatario (Gerente General/Administrador UN), datos del representante legal y razón social, RUC, resolución ARCOTEL, alcance (postes, ductos m, cobertura, provincias, tipo de redes), tabla de rutas propuestas, información del proyecto (objetivo, tipo de infraestructura, cronograma), información técnica/administrativa (representante legal, responsable técnico, coordinador de campo, contratista), declaraciones y compromisos (MAPOD, MN-TEC-OPE-102, pólizas, SIG anual, etc.), firma.

### 9.3 Informe de factibilidad técnica

Plantilla con: fecha/ciudad, destinatario (proveedor), antecedentes (oficio, código CNEL-CORP-SEG-…, razón social, RUC, cobertura, ubicaciones por provincia/cantones/UN, infraestructura requerida, enlace Drive con SIG), verificación realizada (revisión documental, validación SIG con validador y fecha, % cumplimiento, inspección de campo con período/rutas/personal), tabla de resultados técnicos (solicitado/viable/no viable/observaciones para postes y ductos, % factibilidad), conclusiones y recomendación de firma de contrato, firma del Coordinador de Gestión de Arriendo.

### 9.4 Solicitud de ampliación de postes

Plantilla con: número consecutivo de ampliación, fecha, destinatario (Administrador de Contrato), referencias (No. contrato/fecha, última ampliación), resumen ejecutivo (postes/ductos actual/ampliación/total), detalle técnico de rutas a ampliar (coordenadas, totales), justificación técnica (motivación seleccionable), detalles de actividad (ubicación ArcGIS/Google Earth, geodatabase SIG, cronograma), personal técnico asignado, compromisos del proveedor, firma.

### 9.5 Certificado de autorización de incremento/reducción de postes

Documento emitido por el Administrador de Contrato al aprobar una ampliación (cláusula 5.2 del modelo).

---

## 10. API (superficie principal)

REST con prefijo `/api/v1`, documentada con OpenAPI (`/docs`). Autenticación Bearer JWT. Todos los listados con paginación, filtros y orden. Respuestas con códigos HTTP correctos y errores estructurados.

Grupos de endpoints (no exhaustivo):

```
POST   /auth/login                 (local / proveedor)
POST   /auth/login/ad              (dominio Windows / LDAP)
POST   /auth/refresh
POST   /auth/logout

GET    /unidades-negocio
GET    /usuarios                   (admin)

CRUD   /operadoras                 (CableOperadora + hijas)
CRUD   /contratos
POST   /contratos/{id}/documento   (genera contrato desde plantilla)

CRUD   /alquileres                 (AlquilerAnual + PostePorZona)
POST   /alquileres/generar-anio    (manual, idempotente)

CRUD   /solicitudes
POST   /solicitudes/{id}/transicion (workflow: aprobar/observar/rechazar)
GET    /solicitudes/{id}/timeline

CRUD   /facturas
CRUD   /pagos
GET    /reportes/morosidad
POST   /pagos/conciliar

CRUD   /informes-factibilidad
POST   /informes-factibilidad/{id}/documento

CRUD   /novedades
POST   /novedades/{id}/fotos

POST   /documentos                 (upload validado)
GET    /documentos/{id}            (descarga auditada)

GET    /alertas
GET    /dashboard/consolidado      (Matriz: solo lectura)
GET    /auditoria                  (logs, admin)
```

---

## 11. Documentación requerida del proveedor (checklist validable)

El portal y el módulo de autorizaciones deben validar la presencia y estado de estos documentos (mapear a `Documento.tipo_documento`):

**A. Legal y administrativa**
1. Solicitud formal firmada (Anexo 2), con número de referencia, dirigida al destinatario correcto según cobertura; incluir nombres comerciales y foto de placas/etiquetado de chaquetas.
2. Título habilitante ARCOTEL vigente (número de registro, emisión/vigencia, servicios autorizados, cobertura). Excepción: oficio de trámite ante ARCOTEL.
3. Documentación societaria (registro mercantil, nombramiento del representante legal vigente).
4. RUC con emisión ≤ 30 días, estado ACTIVO, actividad de telecomunicaciones, dirección y obligaciones al día.
5. Cédula a color del representante legal (ambos lados); extranjeros: pasaporte y visa vigente.

**B. Financiera y garantías**
6. Comprobante del último pago de energía a CNEL EP de todos los suministros a su nombre.
7. Póliza de Responsabilidad Civil y daños a terceros; cobertura mínima 20% del valor total del contrato; mínimo USD 10.000; vigencia por todo el período contractual.

**C. Técnica del proyecto**
8. Plan de expansión bianual (postes/ductos por cantón + año de instalación + cronograma).
9. Información geoespacial: File Geodatabase SIG compatible ArcGIS 10+, WGS84 / UTM Zona 17S, postes a utilizar (puntos) con ruta del primer año y lo ya utilizado. (Tras la firma, 90 días para entregar la base completa según GU-TEC-OPE-102.)
10. Especificaciones técnicas (memoria técnica: equipos activos, dimensiones, peso, consumo, anclaje).
11. Listado de contactos (administrativo y técnico por zonas: nombre, cédula, teléfono, correo, zona de cobertura).

Cada ítem tiene estado `PENDIENTE/VALIDADO/OBSERVADO/RECHAZADO` y observación. La solicitud no avanza a aprobación gerencial hasta tener cumplimiento documental al 100% (o subsanaciones registradas).

---

## 12. Estructura del monorepositorio

```
sgaie/
├── README.md
├── ESPECIFICACION_TECNICA.md         # este documento
├── docker-compose.yml                # MariaDB + backend + frontend (desarrollo)
├── package.json                      # workspaces pnpm (raíz)
├── pnpm-workspace.yaml
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py                   # FastAPI app, middlewares (CORS, rate limit, seguridad)
│   │   ├── core/                     # config, seguridad (JWT, AES), dependencias
│   │   ├── auth/                     # login local + LDAP/AD, refresh tokens
│   │   ├── db/                       # engine, sesión, base
│   │   ├── models/                   # SQLAlchemy (una por entidad de §6)
│   │   ├── schemas/                  # Pydantic
│   │   ├── services/                 # lógica de negocio + filtro por UN
│   │   ├── routers/                  # endpoints (§10)
│   │   ├── jobs/                     # APScheduler (generación anual, alertas)
│   │   ├── documentos/              # generación docx desde plantillas
│   │   └── auditoria/                # logging de auditoría
│   ├── migrations/                   # Alembic
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── app/                      # router, layout, providers
│   │   ├── api/                      # axios + TanStack Query hooks
│   │   ├── auth/                     # login (dominio/usuario), guard de rutas
│   │   ├── components/               # UI reutilizable
│   │   ├── features/                 # operadoras, contratos, alquileres, pagos,
│   │   │                             #   solicitudes, autorizaciones, novedades
│   │   ├── portal/                   # portal externo del proveedor
│   │   └── lib/
│   └── index.html
│
├── infra/
│   ├── plantillas/                   # .docx/.dotx (contrato, solicitud, informe, ampliación)
│   ├── windows/                      # scripts PowerShell de despliegue + NSSM/servicio
│   └── nginx-or-iis/                 # config reverse proxy + TLS
│
└── docs/
    └── despliegue-windows-server.md
```

---

## 13. Fases de desarrollo (orden sugerido)

| Fase | Entregable |
|---|---|
| **0. Base** | Monorepo, Docker Compose, conexión MariaDB, esqueleto FastAPI + React, CI de linters. |
| **1. Seguridad y acceso** | Auth local + LDAP/AD, JWT + refresh, RBAC, modelo Matriz/UN, auditoría, middlewares de seguridad (§4). |
| **2. Núcleo de datos** | Entidades UnidadNegocio, Usuario, CableOperadora, Contrato, CatalogoCanon + CRUD + UI. |
| **3. Postes y alquileres** | AlquilerAnual + PostePorZona, cálculo de canon, job de auto-generación anual. |
| **4. Solicitudes + workflow** | Portal externo de proveedores, Solicitud, motor de autorizaciones, notificaciones. |
| **5. Documentos** | Carga validada, checklist, generación de plantillas (contrato/solicitud/informe/ampliación). |
| **6. Pagos** | Factura, Pago, conciliación, morosidad, intereses por mora, pasarela (adaptador). |
| **7. Novedades** | Inspecciones, daños, mantenimiento, fotos + geolocalización (mapa). |
| **8. Dashboards y alertas** | Vista consolidada Matriz, alertas de vencimiento, reportes. |
| **9. Despliegue Windows** | Servicio Windows, reverse proxy + TLS, tareas programadas, scripts e instructivo. |

---

## 14. Criterios de aceptación

- La Matriz puede consultar datos de todas las UN pero **no puede** modificar nada (verificado en backend, no solo UI).
- Una UN solo ve y edita registros con su `unidad_negocio_id`.
- Login funciona por **dominio Windows** y por **usuario/clave**, ambos emitiendo JWT + refresh.
- El job del **1 de enero** crea los `AlquilerAnual` del nuevo año de forma idempotente.
- El portal externo permite registro, solicitud (nueva y ampliación), carga de SIG `.zip` y seguimiento de estado.
- El workflow recorre las etapas con comentarios, adjuntos, notificaciones e historial.
- Se generan los documentos (contrato, solicitud, informe de factibilidad, ampliación) con datos reales del expediente.
- Controles de seguridad de §4 presentes y verificables (rate limiting, CORS, cifrado AES-256 de campos 🔒, validación anti-SQLi/XSS, auditoría).
- La aplicación se instala y corre en **Windows Server** con su BD MariaDB y reverse proxy con HTTPS.
- Cobertura de pruebas en backend para servicios críticos (auth, filtro por UN, cálculo de canon, generación anual, workflow).

---

## 15. Supuestos y pendientes a confirmar

- Proveedor de **pasarela de pagos** (integración como adaptador desacoplado).
- Estructura exacta del **Active Directory** institucional (OU, grupos → mapeo a roles/UN).
- Formato de **factura electrónica** (esquema XML del SRI Ecuador) para validación.
- Esquema de **firma electrónica** del contrato final (BCE / proveedor de firma).
- Política de retención y respaldo de archivos SIG (pueden ser pesados).
- Plazos SLA por etapa del workflow.

> Donde un dato no esté disponible, Claude Code debe implementar un valor por defecto razonable y marcarlo con `# TODO: confirmar con cliente`.
