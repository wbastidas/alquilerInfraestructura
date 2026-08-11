# Especificación — Aplicación Móvil de Campo SIG Offline (SGAIE-Móvil)

> Componente adicional del monorepo SGAIE. Documento de diseño/esquema — sin
> código todavía. Referencia: `ESPECIFICACION_TECNICA.md` (raíz) para el
> sistema núcleo (backend/frontend web) con el que este componente se
> relaciona.

---

## 0. Alcance y relación con SGAIE

Esta app es un **componente extra**, independiente en su ciclo de vida
(repositorio Android nativo dentro del mismo monorepo), pero **parte del
proceso** operativo de CNEL EP:

- Extrae de **ArcGIS** (la fuente de verdad geoespacial existente de CNEL EP,
  §2 de `ESPECIFICACION_TECNICA.md`: SIG/GIS, File Geodatabase, WGS84/UTM 17S)
  los **sectores de trabajo** que el personal técnico debe inspeccionar en
  campo.
- Permite trabajar **completamente offline** (sin cobertura de datos en el
  campo): visualizar mapa base, editar el modelo de red (postes, tramos,
  equipos), tomar fotos georreferenciadas y dejar notas de campo.
- **Sincroniza de vuelta hacia ArcGIS** cuando recupera conectividad — ArcGIS
  sigue siendo el repositorio geoespacial autoritativo; esta app **no
  reemplaza** la base SIG, la **opera en campo**.
- Conceptualmente, el trabajo que aquí se hace alimenta dos piezas que ya
  existen en el backend de SGAIE (aunque la integración directa vía API es
  **fase 2**, ver §10):
  - Las **notas de aceptación de ruta** son el equivalente de campo de
    `InformeFactibilidad.rutas_verificadas` / `inspeccion_fecha_inicio` /
    `personal_participante` (§6.9) — la inspección técnica que sustenta la
    revisión de una `Solicitud` en la etapa `REVISION_TECNICA` (§8).
  - Las **notas de incumplimiento de normativa** son el equivalente de campo
    de `Novedad` tipo `DANO_REPORTADO` (§6.13) — y reutilizan exactamente el
    mismo patrón de fotografía geolocalizada que `FotografiaNovedad`
    (`latitud`/`longitud` decimales) ya implementado en
    `backend/app/services/novedad.py`, para que una futura sincronización
    hacia el backend sea un mapeo directo de campos.
- Usuario principal: rol `UN_DELEGADO_TECNICO` (§2.1) — quien hoy ya hace
  "revisión técnica, informe de factibilidad, registro de novedades" en el
  modelo de roles del backend.

---

## 1. Objetivo

App Android nativa para personal técnico de campo que:

1. Extrae de ArcGIS, por sector de trabajo, la cartografía y el modelo de
   red de telecomunicaciones (postes, redes, equipos).
2. Permite trabajar sin conexión: ver mapa offline, crear/editar/eliminar
   elementos de red, registrar notas de incumplimiento normativo y de
   aceptación/rechazo de rutas propuestas, y tomar fotografías con metadata
   de ubicación.
3. Soporta **inspecciones masivas** (recorrer un sector completo verificando
   elemento por elemento, no solo incidentes puntuales).
4. Sincroniza los cambios de vuelta a ArcGIS al recuperar conectividad.

---

## 2. Actores y casos de uso

| Actor | Casos de uso |
|---|---|
| **Delegado Técnico** (`UN_DELEGADO_TECNICO`) | Descargar sector de trabajo, inspeccionar postes/redes/equipos, registrar incumplimientos, aceptar/rechazar rutas propuestas, fotografiar evidencia, sincronizar al volver a cobertura. |
| **Coordinador de campo** | Definir/asignar sectores de trabajo a cuadrillas, revisar el avance de inspecciones masivas, consultar el estado de sincronización. |
| **Administrador SIG (back-office, vía ArcGIS)** | Define los Feature Services "sync enabled" de origen, resuelve conflictos de sincronización no automáticos. |

Casos de uso principales:

- **Extraer sector de trabajo** (online): elegir un sector por extensión
  geográfica o por atributo (p. ej. contrato/operadora) → descarga local.
- **Inspección masiva** (offline): recorrer todos los elementos planificados
  de un sector, marcando cada uno como conforme / con incumplimiento /
  no encontrado.
- **CRUD de elementos de red** (offline): agregar poste nuevo encontrado en
  campo, editar atributos, marcar eliminado (p. ej. poste retirado).
- **Nota de incumplimiento de normativa** (offline): asociar a un elemento
  una observación tipificada según el catálogo MAPOD (ver §4.5).
- **Nota de aceptación de ruta** (offline): validar/rechazar/observar una
  ruta propuesta verificada en terreno.
- **Captura fotográfica geolocalizada** (offline): asociada a cualquier
  elemento o nota.
- **Sincronizar** (online): subir la cola de cambios pendientes a ArcGIS,
  resolver conflictos.

---

## 3. Arquitectura general

### 3.1 Principios

- **Offline-first**: ninguna funcionalidad de campo (ver mapa, editar,
  fotografiar, anotar) depende de tener conectividad.
- **ArcGIS sigue siendo la fuente de verdad geoespacial**: esta app es un
  cliente de edición desconectada, no una base paralela permanente.
- **Mapa base 100% open source**: no se usa el servicio de teselas/basemap
  de ArcGIS (evita dependencia de licenciamiento de Runtime/tiles por
  consumo); solo se usa la **REST API de ArcGIS** para extracción y
  sincronización de datos (que ya forma parte de la infraestructura
  existente de CNEL EP).
- **Estándar abierto para datos**: el almacenamiento local es **GeoPackage**
  (OGC), no un SQLite ad-hoc — así el archivo es inspeccionable/portable con
  QGIS o ArcGIS Pro si se necesita revisión manual.
- Nativo Android (Kotlin), sin frameworks cross-platform, para acceso
  directo y confiable a GPS, cámara y almacenamiento — consistente con el
  criterio de "stack estándar, sin abstracciones exóticas" del proyecto
  (§3.1 de `ESPECIFICACION_TECNICA.md`).

### 3.2 Stack tecnológico propuesto

| Capa | Tecnología | Motivo |
|---|---|---|
| UI | Kotlin + Jetpack Compose | nativo, soporte oficial Android, acceso directo a sensores |
| Almacenamiento local | **GeoPackage** (vía librería NGA GeoPackage Android / SQLite) | estándar OGC abierto, compatible con QGIS/ArcGIS Pro para auditoría |
| Mapa offline | **MapLibre GL Native** (fork open-source de Mapbox GL) + vector/raster tiles (MBTiles/PMTiles) pregenerados de OpenStreetMap | sin licencia comercial, renderizado offline real |
| Extracción/sync con SIG | **ArcGIS REST API** (`createReplica` / `synchronizeReplica` / `applyEdits` sobre Feature Services "sync enabled") | reutiliza la infraestructura ArcGIS ya existente sin requerir el Runtime SDK completo (evita licenciamiento adicional) |
| Fotos + geolocalización | CameraX + FusedLocationProviderClient, EXIF con lat/long/altitud/precisión | estándar Android, sin dependencias externas |
| Sync en segundo plano | WorkManager | reintentos y ejecución diferida cuando hay conectividad |
| Cifrado local (opcional, recomendado) | SQLCipher sobre el GeoPackage | consistente con el principio de cifrado en reposo del backend (§4.4) si el dispositivo se pierde/roba |

### 3.3 Flujo general

```
[ArcGIS Feature Service]
        │  (1) createReplica — filtro por sector (extensión/atributo)
        ▼
[Descarga inicial]  ──► transformación a GeoPackage local
        │
        ▼
[Trabajo 100% OFFLINE]
   - ver mapa base (tiles OSM offline)
   - ver/editar postes, redes, equipos
   - notas de incumplimiento / aceptación de ruta
   - fotos geolocalizadas
   - inspección masiva del sector
        │  cada cambio → fila en cola_sincronizacion (con global_id)
        ▼
[Recupera conectividad]
        │  (2) synchronizeReplica / applyEdits — sube la cola
        ▼
[ArcGIS Feature Service]  ──► resolución de conflictos (ver §5.4)
```

---

## 4. Modelo de datos (GeoPackage)

Convenciones: todas las tablas incluyen `id` (PK local autoincremental),
`global_id` (GUID — debe coincidir con el `GlobalID` de ArcGIS para poder
hacer match en la sincronización), `creado_en`, `actualizado_en`, y
`operacion_pendiente` (enum `NINGUNA` / `CREAR` / `EDITAR` / `ELIMINAR`) que
marca si el registro tiene cambios sin sincronizar.

### 4.1 `sector_trabajo`
Define el área/lote de trabajo descargado de ArcGIS.

| Campo | Tipo | Notas |
|---|---|---|
| `codigo` | texto | identificador del sector (p. ej. asignado por el coordinador) |
| `nombre` | texto | |
| `geometria` | POLYGON | extensión geográfica del sector |
| `contrato_id_referencia` | int, nullable | referencia al `Contrato.id` del backend SGAIE, si aplica |
| `unidad_negocio_id` | int | igual alcance por UN que el resto del sistema (§5.2) |
| `fecha_extraccion` | fecha/hora | cuándo se descargó de ArcGIS |
| `fecha_ultima_sync` | fecha/hora, nullable | |
| `estado` | enum: `DESCARGADO`, `EN_TRABAJO`, `PENDIENTE_SYNC`, `SINCRONIZADO`, `CON_CONFLICTOS` | |
| `usuario_responsable` | texto | usuario/cuadrilla asignada |

### 4.2 `poste`

| Campo | Tipo | Notas |
|---|---|---|
| `sector_trabajo_id` | FK | |
| `codigo_poste` | texto | código de placa/etiqueta física |
| `geometria` | POINT | |
| `tipo_poste` | enum: `HORMIGON`, `MADERA`, `METALICO`, `OTRO` | |
| `altura_m` | decimal | |
| `capacidad_cables` | int | máx. cables soportados (regla del modelo de contrato: 2 transporte + 8 abonado + 1 elemento de red, §9.1) |
| `estado_fisico` | enum: `BUENO`, `REGULAR`, `MALO`, `RETIRADO` | |
| `fecha_inspeccion` | fecha/hora, nullable | |
| `observaciones` | texto | |

### 4.3 `tramo_red`
Tramo de red entre dos postes (o trazado libre).

| Campo | Tipo | Notas |
|---|---|---|
| `sector_trabajo_id` | FK | |
| `poste_origen_id` | FK `poste`, nullable | |
| `poste_destino_id` | FK `poste`, nullable | |
| `geometria` | LINESTRING | |
| `tipo_red` | enum: `FIBRA_OPTICA`, `COAXIAL`, `ELECTRICA`, `OTRO` | coincide con `tipo_redes` de `Solicitud`, §6.7 |
| `longitud_m` | decimal | |
| `estado` | enum: `ACTIVA`, `INACTIVA`, `RETIRADA` | |

### 4.4 `equipo_telecomunicacion`

| Campo | Tipo | Notas |
|---|---|---|
| `poste_id` | FK `poste`, nullable | nullable si el equipo no está montado en poste registrado |
| `tipo_equipo` | enum: `SPLITTER`, `CAJA_EMPALME`, `AMPLIFICADOR`, `ONT`, `OTRO` | |
| `marca`, `modelo` | texto | |
| `numero_serie` | texto | |
| `fecha_instalacion` | fecha, nullable | |
| `estado` | enum: `OPERATIVO`, `DAÑADO`, `RETIRADO` | |

### 4.5 `nota_incumplimiento`
Equivalente de campo a `Novedad` (§6.13), tipo incidente/incumplimiento.

| Campo | Tipo | Notas |
|---|---|---|
| `entidad_tipo` | enum: `POSTE`, `TRAMO_RED`, `EQUIPO`, `SECTOR` | polimórfico, igual patrón que `Documento.entidad_tipo` (§6.8) |
| `entidad_id` | int | |
| `tipo_incumplimiento` | enum (catálogo MAPOD — ver nota abajo) | `# TODO: confirmar catálogo cerrado de incumplimientos con el área normativa de CNEL EP` |
| `descripcion` | texto | |
| `gravedad` | enum: `LEVE`, `MODERADA`, `GRAVE` | |
| `fecha` | fecha/hora | |
| `estado_subsanacion` | enum: `PENDIENTE`, `NOTIFICADO`, `SUBSANADO` | |

> Catálogo de incumplimiento sugerido por defecto (ajustable): exceso de
> cables por poste, cableado sin orden/etiquetado, poste en mal estado
> estructural, equipo sin autorización registrada, ruta fuera de lo
> aprobado, falta de señalización/etiquetado de chaquetas.

### 4.6 `nota_aceptacion_ruta`
Equivalente de campo a la verificación de `InformeFactibilidad.rutas_verificadas` (§6.9).

| Campo | Tipo | Notas |
|---|---|---|
| `sector_trabajo_id` | FK | |
| `ruta_referencia` | texto, nullable | referencia a `RutaPropuesta` del backend (provincia/ciudad/recinto), si la ruta proviene de una `Solicitud` existente |
| `geometria` | LINESTRING, nullable | trazado verificado en campo (puede diferir del propuesto) |
| `decision` | enum: `ACEPTADA`, `ACEPTADA_CON_OBSERVACIONES`, `RECHAZADA` | |
| `comentario` | texto | |
| `fecha` | fecha/hora | |

### 4.7 `fotografia`
Mismo patrón que `FotografiaNovedad` del backend (`latitud`/`longitud`).

| Campo | Tipo | Notas |
|---|---|---|
| `entidad_tipo` | enum: `POSTE`, `TRAMO_RED`, `EQUIPO`, `NOTA_INCUMPLIMIENTO`, `NOTA_ACEPTACION_RUTA` | |
| `entidad_id` | int | |
| `ruta_archivo_local` | texto | ruta en almacenamiento del dispositivo |
| `latitud`, `longitud` | decimal | de EXIF/GPS al momento de captura |
| `altitud_m`, `precision_gps_m` | decimal, nullable | |
| `acimut_grados` | decimal, nullable | orientación de la brújula al capturar |
| `timestamp_captura` | fecha/hora | |
| `hash_sha256` | texto | integridad, mismo criterio que `Documento.hash_sha256` (§6.8) |
| `sincronizada` | bool | |

### 4.8 `inspeccion_masiva` / `inspeccion_detalle`
Para recorridos sistemáticos de un sector completo (no solo incidentes puntuales).

**`inspeccion_masiva`**: `sector_trabajo_id`, `fecha_inicio`, `fecha_fin`,
`usuario_responsable`, `total_elementos_planificados`,
`total_elementos_inspeccionados`, `estado` (`EN_CURSO`/`COMPLETADA`).

**`inspeccion_detalle`**: `inspeccion_masiva_id`, `entidad_tipo`,
`entidad_id`, `resultado` (`OK`/`INCUMPLIMIENTO`/`NO_ENCONTRADO`),
`nota_incumplimiento_id` (FK nullable).

### 4.9 `cola_sincronizacion`
Cola de cambios pendientes de subir a ArcGIS (patrón outbox).

| Campo | Tipo | Notas |
|---|---|---|
| `entidad_tipo`, `entidad_id` | — | qué cambió |
| `operacion` | enum: `CREAR`, `EDITAR`, `ELIMINAR` | |
| `payload_json` | texto | snapshot del registro al momento del cambio |
| `intentos` | int | |
| `estado` | enum: `PENDIENTE`, `ENVIADO`, `ERROR` | |
| `mensaje_error` | texto, nullable | |

---

## 5. Sincronización con ArcGIS

### 5.1 Extracción de sectores (online, requiere conectividad)

1. El usuario selecciona/recibe un sector de trabajo (por extensión
   geográfica dibujada en el mapa, o por atributo — p. ej. número de
   contrato/operadora).
2. La app llama la operación `createReplica` de la REST API de ArcGIS sobre
   el/los Feature Service(s) de origen ("sync enabled"), con el filtro
   geográfico/atributo del sector.
3. La respuesta (geodatabase de réplica) se transforma a las tablas
   GeoPackage locales (§4), conservando el `GlobalID` de ArcGIS como
   `global_id` local — esta es la clave para el matching de conflictos.
4. Se crea el registro `sector_trabajo` con estado `DESCARGADO`.

### 5.2 Edición offline

Toda alta/edición/eliminación local:
- Modifica directamente la tabla GeoPackage correspondiente.
- Encola un registro en `cola_sincronizacion` con el payload completo.
- Si el elemento es nuevo (creado en campo, sin `global_id` de ArcGIS aún),
  se le asigna un GUID local temporal que ArcGIS reemplazará por el
  `GlobalID` definitivo al sincronizar.

### 5.3 Sincronización de cambios (online)

1. Al detectar conectividad (o manualmente), `WorkManager` dispara el
   sincronizador.
2. Se recorre `cola_sincronizacion` en estado `PENDIENTE` y se agrupan por
   Feature Service de destino.
3. Se invoca `synchronizeReplica` (o `applyEdits` para altas/ediciones/
   bajas directas si el flujo no usa réplicas completas) con los cambios.
4. Por cada elemento aceptado: se marca `ENVIADO`, se actualiza el
   `global_id` si era temporal, y se limpia `operacion_pendiente`.
5. Por cada elemento rechazado: se marca `ERROR` con el mensaje devuelto por
   ArcGIS, sin perder el dato local (reintentable).
6. Las fotografías se suben como adjuntos de su entidad relacionada
   (`addAttachment` de la REST API) en el mismo ciclo.

### 5.4 Resolución de conflictos

- **Edición concurrente del mismo elemento** (editado en ArcGIS y en el
  dispositivo desde la última extracción): estrategia por defecto
  *"el cambio de campo gana"* salvo que ArcGIS reporte un conflicto de
  eliminación (elemento borrado en el servidor mientras se editaba en
  campo) — ese caso siempre queda marcado `CON_CONFLICTOS` para revisión
  manual del coordinador, nunca se resuelve automáticamente perdiendo
  trabajo de campo en silencio.
- Todo conflicto no resuelto automáticamente queda visible en una pantalla
  de "Conflictos pendientes" dentro de la app, con el detalle de ambas
  versiones.

---

## 6. Mapa offline open source

- Tiles base de **OpenStreetMap** pregeneradas (raster MBTiles o vector
  PMTiles) y empaquetadas/descargadas en el dispositivo **antes** de la
  salida a campo (por región o por sector de trabajo, para no ocupar
  almacenamiento innecesario).
- Renderizado con **MapLibre GL Native** (Android), sin llamadas a servicios
  externos durante el trabajo de campo.
- Capas superpuestas (postes/tramos/equipos/sector) se dibujan directamente
  desde el GeoPackage local — coherente con el estándar OGC, sin
  reprocesamiento adicional.
- Simbología diferenciada por `estado_fisico` / `tipo_red` / presencia de
  `nota_incumplimiento` asociada (p. ej. poste con incumplimiento pendiente
  resaltado en rojo).

---

## 7. Fotografías geolocalizadas

- Captura vía CameraX; ubicación vía `FusedLocationProviderClient` (último
  fix de alta precisión disponible, con indicador de precisión en metros).
- Metadata EXIF embebida (lat/long/altitud) **además** de los campos
  explícitos en `fotografia` (§4.7), para que el archivo sea autocontenible
  si se exporta fuera de la app.
- Mismo criterio de integridad que `Documento.hash_sha256` del backend
  (§6.8): cada foto se hashea al capturarse, para detectar alteraciones
  antes de sincronizar.

---

## 8. Inspecciones masivas

Modo de trabajo distinto al de "incidente puntual": el usuario abre una
`inspeccion_masiva` sobre un `sector_trabajo`, y la app genera la lista de
`inspeccion_detalle` a partir de **todos** los postes/tramos/equipos del
sector (no solo los que tengan una nota previa). El flujo de campo es
"recorrer la lista, marcar cada elemento" en vez de "buscar el elemento con
problema" — pensado para auditorías periódicas completas de un sector
(p. ej. validar `postes_sig` vs. `postes_fisicos`, §6.6/§7.2 del backend) y
no solo para reportar daños puntuales.

---

## 9. Seguridad

Consistente con los principios transversales del backend (§4 de
`ESPECIFICACION_TECNICA.md`), adaptados a un dispositivo móvil que puede
perderse/robarse:

- Autenticación contra ArcGIS con OAuth2 (token de la organización ArcGIs
  Online/Enterprise de CNEL EP); el token **no** se reutiliza como mecanismo
  de login a SGAIE-web (sistemas independientes en esta fase, ver §10).
- GeoPackage local cifrado en disco (SQLCipher) — protege datos de campo
  si el dispositivo se pierde, mismo principio que el cifrado en reposo del
  backend (§4.4).
- Bloqueo de sesión por inactividad / PIN de la app, independiente del
  bloqueo del sistema operativo.
- Fotografías y notas no se comparten fuera de los canales de sincronización
  definidos (sin "compartir a" genérico de Android hacia apps externas).

---

## 10. Integración con el backend SGAIE (opcional / fase 2)

Fuera del alcance inmediato (la sincronización primaria es **app ↔
ArcGIS**), pero se deja documentado como extensión natural una vez validado
el flujo con ArcGIS:

- Endpoint nuevo en el backend (p. ej. `POST /novedades/desde-movil`) que
  reciba `nota_incumplimiento` ya sincronizadas y las traduzca a `Novedad`
  (§6.13), reutilizando el servicio existente `app/services/novedad.py`.
- Igual idea para `nota_aceptacion_ruta` → alimentar
  `InformeFactibilidad.rutas_verificadas` durante la etapa
  `REVISION_TECNICA` de una `Solicitud` (§8).
- Requeriría que la app autentique también contra el backend SGAIE (JWT),
  además de contra ArcGIS — dos sistemas de identidad distintos a
  reconciliar; **no se asume nada aquí sin confirmación del cliente**.

`# TODO: confirmar con CNEL EP si esta integración bidireccional con el backend SGAIE es necesaria en el corto plazo, o si ArcGIS sigue siendo el único destino de sincronización por ahora.`

---

## 11. Estructura propuesta del componente en el monorepo

```
mobile/
├── ESPECIFICACION_MOVIL_OFFLINE.md   # este documento
└── android/                          # (a crear cuando inicie la implementación)
    ├── app/                          # módulo Kotlin/Compose principal
    ├── data/                         # GeoPackage, DAOs, cola de sincronización
    ├── sync/                         # cliente REST de ArcGIS, WorkManager
    └── map/                          # integración MapLibre + tiles offline
```

No se generó código todavía — este documento es el esquema/diseño previo a
la implementación.

---

## 12. Fases de desarrollo sugeridas

| Fase | Entregable |
|---|---|
| **M0. Esquema** | Este documento (modelo de datos, arquitectura, sync). |
| **M1. Mapa offline** | Descarga/empaquetado de tiles OSM, render con MapLibre, sin datos de ArcGIS todavía. |
| **M2. Extracción ArcGIS → GeoPackage** | `createReplica` por sector, transformación a GeoPackage, visualización de capas sobre el mapa offline. |
| **M3. CRUD offline + cola de sincronización** | Edición de postes/redes/equipos, notas de incumplimiento y de aceptación de ruta, outbox pattern. |
| **M4. Fotografías geolocalizadas** | Captura, EXIF, hash, vínculo a entidades. |
| **M5. Sincronización de vuelta + conflictos** | `synchronizeReplica`/`applyEdits`, pantalla de conflictos pendientes. |
| **M6. Inspección masiva** | Generación de listas de verificación por sector, seguimiento de avance. |
| **M7. Integración SGAIE (opcional)** | Puente hacia `Novedad`/`InformeFactibilidad` del backend (§10), sujeto a confirmación con el cliente. |

---

## 13. Supuestos y pendientes a confirmar

- Catálogo cerrado de tipos de incumplimiento normativo (hoy es una lista
  default editable, §4.5) — pendiente de validar con el área normativa/MAPOD
  de CNEL EP.
- Si los Feature Services de ArcGIS de CNEL EP ya tienen **sync habilitado**
  (`isDataVersioned`/`syncEnabled`) — requisito técnico indispensable para
  `createReplica`/`synchronizeReplica`; si no, requiere configuración previa
  del lado de administración SIG.
- Política de retención de fotografías de campo en el dispositivo tras
  sincronizar (¿se borran localmente o se conservan como caché?).
- Si se requiere integración con el backend SGAIE (§10) en el corto o
  mediano plazo, o si por ahora ArcGIS es el único destino.
- Tamaño máximo/ esperado de un "sector de trabajo" (para dimensionar el
  empaquetado de tiles offline y el volumen de features por réplica).
