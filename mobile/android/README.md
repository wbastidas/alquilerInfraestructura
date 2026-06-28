# SGAIE Móvil — Android (scaffold M1+M2+M3+M4+M5)

Proyecto Android nativo del componente móvil descrito en
`mobile/ESPECIFICACION_MOVIL_OFFLINE.md`. Este scaffold cubre las fases
**M1** (mapa offline con MapLibre, empaquetado de tiles vía MBTiles),
**M2** (extracción ArcGIS → GeoPackage, visualización de capas), **M3**
(CRUD offline de postes/redes/equipos, notas de incumplimiento y de
aceptación de ruta, cola de sincronización), **M4** (fotografías
geolocalizadas con metadata EXIF y hash de integridad) y **M5**
(sincronización de vuelta a ArcGIS vía `applyEdits`/`addAttachment`,
resolución manual de conflictos, sincronización periódica en segundo
plano) del roadmap (§12).

## Qué incluye este scaffold

### M1 — mapa offline

- Proyecto Gradle (Kotlin DSL) con un único módulo `:app`.
- Jetpack Compose + Material 3 (UI mínima).
- `MapView` de MapLibre embebido en Compose (`map/OfflineMapScreen.kt`),
  estilo construido en memoria (`map/OfflineMapStyleProvider.kt`, sin
  estilos remotos de terceros).
- Servidor HTTP embebido (`map/OfflineTileServer.kt`, NanoHTTPD) que sirve
  un archivo `.mbtiles` local como tiles XYZ en `127.0.0.1`, con la
  conversión de fila TMS→XYZ que requiere el formato MBTiles.

### M2 — extracción ArcGIS → GeoPackage (§5.1, §4, §6)

- Modelo de datos local en GeoPackage (estándar OGC, inspeccionable con
  QGIS/ArcGIS Pro): `data/GeoPackageContract.kt`, `data/GeoPackageProvider.kt`
  y un repositorio por entidad (`SectorTrabajoRepository`, `PosteRepository`,
  `TramoRedRepository`, `EquipoTelecomunicacionRepository`), todos con
  creación de tabla idempotente y `insertar`/`listarPor*`.
- Cliente REST mínimo hacia un Feature Service de ArcGIS "sync enabled"
  (`sync/ArcGisRestClient.kt`): `createReplica` con `dataFormat=sqlite` y
  descarga del archivo resultante (la réplica es en sí misma SQLite, sin
  parser de geodatabase binaria propietario).
- Lectura genérica de la réplica descargada (`sync/ReplicaGeodatabaseReader.kt`)
  y mapeo de columnas a las entidades locales (`sync/FieldMapping.kt`).
- Orquestador de extracción completo (`sync/ArcGisSectorExtractor.kt`):
  `createReplica` → lectura → mapeo → resolución de referencias
  poste-origen/poste-destino/poste-de-equipo por `GlobalID` → escritura en
  los repositorios GeoPackage.
- Capas vectoriales del sector sobre el mapa offline
  (`map/SectorLayersRenderer.kt`): postes, tramos de red y equipos, leídos
  directamente del GeoPackage local y dibujados como `GeoJsonSource` +
  `CircleLayer`/`LineLayer`, con color por `estado_fisico`/`tipo_red`.
- Pantalla "Descargar sector de trabajo" (`map/DescargaSectorScreen.kt`),
  accesible desde el botón flotante del mapa, que captura los datos
  mínimos (URL del servicio, token, extensión geográfica) y dispara el
  orquestador; al finalizar, vuelve al mapa y redibuja las capas.
- `INTERNET`/`ACCESS_NETWORK_STATE` en el manifiesto: única operación
  online del componente (la extracción); el resto del trabajo de campo
  sigue siendo 100% offline.

### Limitaciones explícitas de M2 (pendientes de confirmación con CNEL EP, §13)

- **Sin login OAuth2 real**: el token de ArcGIS se captura manualmente en
  la pantalla de descarga en vez de obtenerse de un flujo de autenticación,
  porque el mecanismo real (OAuth2 de la organización ArcGIS) está
  pendiente de confirmación.
- **Sin dibujo de extensión sobre el mapa**: el rectángulo de extracción se
  captura como 4 campos numéricos (xmin/ymin/xmax/ymax) en vez de
  dibujarse interactivamente sobre el mapa.
- **Nombres de tabla/columna de la réplica sin confirmar**: las constantes
  `TABLA_*`/`COL_*` de `FieldMapping.kt` y `ArcGisSectorExtractor.kt` asumen
  los nombres en español del modelo de datos de este documento; si el
  Feature Service real de CNEL EP expone otros nombres, deben ajustarse.
- **Convención de FK origen/destino sin confirmar**: se asume que
  `poste_origen_id`/`poste_destino_id`/`poste_id` en la réplica contienen el
  `GlobalID` (texto) del poste relacionado, no su `OBJECTID` numérico.
- No se implementó polling de `/createReplica/jobs/{jobId}` (réplica
  asíncrona): se asume `async=false` viable para el tamaño de sector
  esperado; revisar si CNEL EP confirma sectores grandes.

### M3 — CRUD offline + cola de sincronización (§4.5, §4.6, §4.9, §5.2)

- **Cola de sincronización / outbox** (`data/ColaSincronizacionRepository.kt`,
  tabla `cola_sincronizacion`): cada alta/edición/baja local de
  poste/tramo/equipo/nota encola un registro `PENDIENTE` con
  `entidad_tipo`, `entidad_id`, `operacion` (CREAR/EDITAR/ELIMINAR) y un
  snapshot JSON de la entidad, listo para que un futuro worker de sync lo
  envíe a ArcGIS (`applyEdits`). No se implementó aún ese envío (M4+):
  esta fase solo construye el outbox y lo alimenta.
- `actualizar()`/`eliminar()` agregados a `PosteRepository`,
  `TramoRedRepository` y `EquipoTelecomunicacionRepository`: mutan la fila
  GeoPackage (marcando `operacion_pendiente = EDITAR`/`ELIMINAR`) y
  encolan el snapshot correspondiente en la misma operación.
- Notas de campo, ambas con su propio repositorio y tabla GeoPackage
  (`data/NotaIncumplimientoRepository.kt`,
  `data/NotaAceptacionRutaRepository.kt`):
  - `nota_incumplimiento` (§4.5): tipo, descripción, gravedad y estado de
    subsanación sobre la entidad seleccionada (poste/tramo/equipo).
  - `nota_aceptacion_ruta` (§4.6): decisión (ACEPTADA/ACEPTADA_CON_OBSERVACIONES/
    RECHAZADA) y comentario sobre una ruta propuesta del sector.
- Selección de entidad por tap sobre el mapa
  (`map/FeatureSeleccionHandler.kt`), usando la API de features
  renderizados de MapLibre (consulta capa por capa, en orden de
  prioridad equipo→poste→tramo, ya que `queryRenderedFeatures` no indica
  a qué capa pertenece cada resultado cuando se consultan varias a la
  vez), cableada en `map/OfflineMapScreen.kt` vía
  `addOnMapClickListener`.
- Pantallas de edición y de notas (`map/EdicionEntidadScreen.kt`,
  `map/NotaIncumplimientoScreen.kt`, `map/NotaAceptacionRutaScreen.kt`),
  navegadas desde `MainActivity.kt`: tocar una entidad en el mapa abre su
  edición (con accesos a "Eliminar" y "Registrar nota de
  incumplimiento"); un segundo botón flotante en el mapa abre el
  formulario de aceptación de ruta para el sector cargado.

### Limitaciones explícitas de M3 (pendientes de confirmación con CNEL EP, §13)

- **Catálogo de `TipoIncumplimiento` sin confirmar**: los valores del
  enum en `data/GeoPackageContract.kt` son un catálogo de referencia, no
  el catálogo cerrado real (pendiente con el área normativa/MAPOD de
  CNEL EP).
- **Sin dibujo interactivo del trazado verificado**: igual que la
  extensión geográfica de M2, `nota_aceptacion_ruta` tiene una columna de
  geometría `LINESTRING` opcional en el modelo, pero la UI
  (`NotaAceptacionRutaScreen.kt`) todavía no permite dibujarla sobre el
  mapa; la nota se guarda sin geometría.
- **Campos enum como texto libre**: los selectores de tipo/estado/gravedad
  en los formularios de edición y notas son `OutlinedTextField` de texto
  libre validados contra el enum al guardar (no hay un componente de
  dropdown/chip en este scaffold todavía), siguiendo el mismo patrón que
  ya usaba `DescargaSectorScreen.kt` en M2.
- **API de bajo nivel de `geopackage-android` sin verificar en este
  sandbox**: `FeatureDao.queryForIdRow`/`.update`/`.deleteById`, usados en
  los nuevos métodos `actualizar()`/`eliminar()`, se escribieron según la
  API pública documentada de la librería, pero no pudieron probarse
  contra una compilación real (ver limitación del entorno más abajo).

### M4 — Fotografías geolocalizadas (§4.7, §7)

- Tabla `fotografia` en GeoPackage (`data/FotografiaRepository.kt`), mismo
  patrón de outbox que las notas de M3: `insertar()` puebla la geometría
  punto (`GeoPackageProvider.geometriaPuntoWgs84`) con la latitud/longitud
  reales de la captura —a diferencia de `nota_incumplimiento`/
  `nota_aceptacion_ruta`, que dejan la geometría opcional sin poblar— y
  encola `CREAR` en `cola_sincronizacion`. `EntidadTipo` se extendió con
  `NOTA_INCUMPLIMIENTO`/`NOTA_ACEPTACION_RUTA` para que una fotografía
  también pueda vincularse a una nota, no solo a poste/tramo/equipo/sector.
- `map/UbicacionProvider.kt`: envuelve
  `FusedLocationProviderClient.getCurrentLocation(PRIORITY_HIGH_ACCURACY, ...)`
  (API listener-based de `play-services-location`) en una función
  `suspend` vía `suspendCancellableCoroutine`, para obtener el "último fix
  de alta precisión disponible" (§7) sin bloquear el hilo principal.
- `map/FotografiaCapturaScreen.kt`: pantalla de captura con CameraX
  (`Preview` + `ImageCapture` enlazados al ciclo de vida vía
  `ProcessCameraProvider`), que solicita en tiempo de ejecución los
  permisos `CAMERA` y `ACCESS_FINE_LOCATION`
  (`rememberLauncherForActivityResult` +
  `ActivityResultContracts.RequestMultiplePermissions`), guarda el JPEG en
  almacenamiento de la app (`getExternalFilesDir("fotografias")`), escribe
  metadata GPS en el EXIF del archivo (`androidx.exifinterface`:
  `setLatLong`/`setAltitude`/`TAG_GPS_H_POSITIONING_ERROR`), calcula su
  hash SHA-256 (integridad, mismo patrón que `Documento.hash_sha256` del
  backend, §6.8) y la inserta vía `FotografiaRepository`.
- Puntos de entrada cableados desde `MainActivity.kt`
  (`Pantalla.FOTOGRAFIA_CAPTURA`, reutilizando `FeatureSeleccionada`):
  botón "Tomar fotografía" en `EdicionEntidadScreen.kt` (poste/tramo/
  equipo) y paso de confirmación "Tomar fotografía de evidencia" tras
  guardar en `NotaIncumplimientoScreen.kt`/`NotaAceptacionRutaScreen.kt`.
- Permiso `CAMERA` + `<uses-feature android:name="android.hardware.camera.any" android:required="false">`
  agregados al manifiesto; `ACCESS_FINE_LOCATION`/`ACCESS_COARSE_LOCATION`
  ya estaban declarados desde M2/M3 pero sin un consumidor real hasta
  ahora.

### Limitaciones explícitas de M4 (pendientes de confirmación con CNEL EP, §13)

- **`acimut_grados` (orientación de la cámara, §4.7) no se captura**: se
  guarda siempre `null`. Requeriría fusión de sensores (acelerómetro +
  magnetómetro vía `SensorManager.getRotationMatrix`/`getOrientation`),
  que no se puede escribir con confianza sin poder compilar/probar contra
  un dispositivo real en este sandbox.
- **API de bajo nivel de CameraX/FusedLocationProviderClient/
  `CancellationTokenSource` sin verificar en este sandbox**: igual que el
  resto del código de bajo nivel de M2/M3, se escribió según la API
  pública documentada de `androidx.camera`/`play-services-location`, pero
  no pudo compilarse ni probarse contra un dispositivo o emulador real
  (ver limitación del entorno más abajo).
- **Sin selector de cámara frontal/trasera ni zoom/flash**: la pantalla de
  captura usa siempre `CameraSelector.DEFAULT_BACK_CAMERA` sin controles
  adicionales, suficiente para el caso de uso de campo descrito en §7
  pero no una app de cámara completa.

### M5 — Sincronización de vuelta + conflictos (§5.3, §5.4)

- `sync/ArcGisRestClient.kt` se extiende con tres métodos: `applyEdits`
  (sube altas/ediciones/bajas a una capa identificando cada feature por
  `GlobalID` vía `useGlobalIds=true`, en vez de requerir una resolución
  previa de OBJECTID), `obtenerObjectIdPorGlobalId` (resuelve el OBJECTID
  asignado por el servidor a partir de un `GlobalID`, único caso que lo
  necesita: `addAttachment` no admite `useGlobalIds`) y `addAttachment`
  (sube un archivo como adjunto de una feature).
- `data/GeoPackageContract.kt` agrega `TablaOrigen` (qué tabla GeoPackage
  generó cada ítem de la cola, ya que `entidad_tipo`/`entidad_id` tienen
  semántica distinta según el origen) y el estado `CONFLICTO` en
  `EstadoSincronizacion` (un rechazo de ArcGIS que la especificación exige
  dejar siempre para revisión manual, distinto de un `ERROR` simple
  reintentable), junto con `TipoConflictoSincronizacion`
  (`ELIMINADO_EN_SERVIDOR`/`ERROR_NO_RECUPERABLE`).
- `data/ConflictoSincronizacionRepository.kt` (tabla
  `conflicto_sincronizacion`): persiste el detalle de cada conflicto no
  resuelto automáticamente (versión local y, si la hay, la del servidor)
  para la pantalla de "Conflictos pendientes".
- `sync/SincronizadorCambios.kt`: orquestador que drena
  `cola_sincronizacion`, agrupa los ítems pendientes de poste/tramo_red/
  equipo por capa y llama `applyEdits` por lotes (reconstruyendo
  atributos+geometría en vivo desde el repositorio correspondiente para
  CREAR/EDITAR, ya que el snapshot JSON de la cola no incluye geometría),
  sube fotografías pendientes vía `addAttachment` resolviendo su OBJECTID,
  clasifica cada resultado en ENVIADO/ERROR/CONFLICTO, y al final
  recalcula `SectorTrabajo.estado` (`CON_CONFLICTOS`/`SINCRONIZADO`) según
  el estado restante de los ítems de cada sector.
- Pantallas `map/SincronizacionScreen.kt` ("Sincronizar ahora", con el
  mismo patrón de captura manual de URL/token de `DescargaSectorScreen`)
  y `map/ConflictosPendientesScreen.kt` (lista ambas versiones de cada
  conflicto con un botón "Descartar"), navegadas desde un tercer botón
  flotante ("⇅") en `map/OfflineMapScreen.kt`.
- `sync/SincronizacionWorker.kt` (`CoroutineWorker` + WorkManager):
  reintenta la sincronización cada 15 minutos (mínimo permitido por
  WorkManager para trabajo periódico) solo con red disponible, reutilizando
  la URL/token de la última sincronización manual exitosa, persistidos en
  `sync/SincronizacionPreferencias.kt` (SharedPreferences). Se programa al
  abrir la app (`MainActivity.onCreate`) y de nuevo tras cada
  sincronización manual.
- `sync/SincronizacionLock.kt`: exclusión mutua (`kotlinx.coroutines.sync.Mutex`)
  para que la extracción de un sector (`DescargaSectorScreen`) y la subida
  de cambios (`SincronizacionScreen` o `SincronizacionWorker` en segundo
  plano) nunca corran en simultáneo **dentro del mismo dispositivo**, ya
  que ambas leen/escriben el mismo GeoPackage local. Los tres disparadores
  intentan `tryLock()` antes de empezar: las dos pantallas muestran un
  error inmediato ("ya hay una sincronización o descarga en curso") si el
  candado está tomado, y el worker periódico simplemente devuelve
  `Result.retry()` para reintentar más tarde. Esto **no** resuelve
  concurrencia *entre* dispositivos distintos —cada dispositivo ya tiene su
  propio GeoPackage y su propia `cola_sincronizacion` (outbox)
  independientes, y llaman directamente a la REST API de ArcGIS, diseñada
  para atender múltiples clientes a la vez—; el único caso cruzado real,
  dos dispositivos editando el mismo elemento, ya lo cubre la resolución de
  conflictos de §5.4 descrita arriba.

### Limitaciones explícitas de M5 (pendientes de confirmación con CNEL EP, §13)

- **`supportsApplyEditsWithGlobalIds` sin confirmar**: `applyEdits` con
  `useGlobalIds=true` requiere que la capa lo soporte en su definición de
  servicio; no se pudo verificar contra un Feature Service real de CNEL EP
  en este sandbox. Si la capa no lo soporta, ArcGIS devuelve error y el
  ítem queda en `ERROR` para revisión manual (nunca se aplica con datos
  incorrectos).
- **Clasificación de conflicto por texto del mensaje de error**: no se
  pudo confirmar el código de error exacto que ArcGIS devuelve para "la
  feature ya no existe en el servidor" (el único caso que §5.4 exige
  dejar siempre para revisión manual); se usa una heurística de texto
  (`"not found"`/`"no encontr"` en la descripción/mensaje del error) para
  distinguirlo de un `ERROR_NO_RECUPERABLE` simple. Debe ajustarse si CNEL
  EP confirma el código real.
- **Alcance de capas sincronizadas**: `applyEdits` solo cubre
  poste/tramo_red/equipo (las únicas con capa ArcGIS confirmada en
  `ArcGisConfig.Capas`); `nota_incumplimiento`/`nota_aceptacion_ruta`
  quedan fuera de alcance de M5 (sin capa confirmada). Las fotografías
  vinculadas a sector o a una nota tampoco se suben (su ítem de cola queda
  `PENDIENTE` indefinidamente, sin marcarse como error, hasta que se
  resuelva esta limitación).
- **FK origen/destino omitidas al reconstruir atributos**: igual que en
  M2, `poste_origen_id`/`poste_destino_id`/`poste_id` no se incluyen en
  los atributos enviados a `applyEdits` (requieren resolver el `GlobalID`
  del lado servidor, no implementado en esta fase).
- **`actualizarEstado`/`queryForIdRow` de bajo nivel sin verificar**: igual
  que el resto de la API de bajo nivel de `geopackage-android` usada en
  este scaffold (ver limitaciones de M3), no se pudo probar contra una
  compilación real.
- **Sin login OAuth2 real**: la URL/token de ArcGIS persistidos para el
  worker periódico son los mismos capturados manualmente en
  `SincronizacionScreen`, guardados sin cifrar en SharedPreferences;
  placeholder hasta tener un flujo OAuth2 real (§9).
- **Resolución de conflictos limitada a "Descartar"**: `ConflictosPendientesScreen`
  solo permite quitar un conflicto de la lista una vez resuelto
  manualmente fuera de la app (p. ej. en ArcGIS Pro); no ofrece "forzar
  reenvío" ni "descartar cambio local" como acciones automáticas.

## Limitación conocida de este entorno (sandbox de desarrollo)

Este contenedor tiene Java 21 y Gradle 8.14.3 instalados, pero **no tiene
el Android SDK** (no hay `cmdline-tools`, `sdkmanager` ni
`ANDROID_HOME`/`local.properties` configurado), y su política de red
bloquea `dl.google.com` (el repositorio Maven de Google donde se publica
el Android Gradle Plugin y la mayoría de artefactos de AndroidX). Validado
en este entorno:

- El wrapper de Gradle (`gradlew`/`gradlew.bat`/`gradle-wrapper.jar`) se
  generó con la distribución de Gradle del sistema y **se verificó
  funcional**: `./gradlew help` descargó la distribución 8.14.3 real
  desde `services.gradle.org` y evaluó correctamente
  `settings.gradle.kts` y `build.gradle.kts` (la sintaxis de ambos
  archivos Kotlin DSL es válida).
- La evaluación falla, como es esperado en este sandbox, al intentar
  resolver el plugin `com.android.application:8.6.1`: Gradle lo busca en
  Google, MavenRepo y el Gradle Plugin Portal y no lo encuentra porque el
  repositorio de Google está bloqueado a nivel de red aquí. En una
  máquina de desarrollo normal (con acceso a `dl.google.com`) este mismo
  comando debería resolver el plugin sin problema.
- Por lo tanto, **no fue posible** ejecutar una compilación real
  (`assembleDebug`) ni verificar la resolución de las dependencias de
  AndroidX/MapLibre/NanoHTTPD en este entorno.
- El código Kotlin/Gradle fue escrito siguiendo las APIs públicas
  estables de MapLibre Android SDK 11.x, AndroidX y NanoHTTPD, pero su
  compilación real debe verificarse en una máquina con Android Studio o
  con acceso de red sin restricciones a `dl.google.com`.
- Las dependencias agregadas en M2 (`mil.nga.geopackage:geopackage-android`,
  `com.squareup.okhttp3:okhttp`) están en Maven Central, no en el
  repositorio de Google, pero **tampoco se pudo verificar su resolución
  real** en este sandbox: la evaluación de Gradle falla antes, al
  resolver el plugin de Android (bloqueado en `dl.google.com`), así que
  nunca llega a intentar resolver las dependencias del módulo `:app`.
  `./gradlew help` sí se volvió a ejecutar tras agregar todo el código de
  M2 y el resultado es el mismo fallo esperado de M1 (plugin de Android no
  resuelto), confirmando que la sintaxis Kotlin/Gradle de los archivos
  nuevos no introdujo errores adicionales de evaluación.

## Cómo validarlo localmente (con Android Studio)

1. Instala Android Studio (incluye el SDK manager).
2. Abre la carpeta `mobile/android/` como proyecto.
3. Al sincronizar, Android Studio creará `local.properties` con la ruta
   real del SDK (o copia `local.properties.example` y ajusta `sdk.dir`).
4. Copia un `.mbtiles` de prueba al dispositivo/emulador en:
   `Android/data/ec.cnel.sgaie.movil/files/tiles/sector-demo.mbtiles`
   (por ejemplo, vía `adb push archivo.mbtiles /sdcard/Android/data/ec.cnel.sgaie.movil/files/tiles/sector-demo.mbtiles`).
5. Ejecuta `./gradlew :app:assembleDebug` o corre la app directamente
   desde Android Studio.
6. Si no copias ningún `.mbtiles`, la app muestra el mensaje
   "No se encontró el paquete de tiles del sector..." en lugar de fallar.

## Próximos pasos (fuera de alcance de M1+M2+M3+M4+M5)

- Sincronización de `nota_incumplimiento`/`nota_aceptacion_ruta` y de las
  fotografías vinculadas a sector/notas (capas ArcGIS sin confirmar).
- Resolución de conflictos más allá de "Descartar" (forzar reenvío,
  descartar cambio local, fusión de versiones).
- Login OAuth2 real (reemplaza la captura manual de URL/token en todas las
  pantallas que la usan), dibujo interactivo de geometrías (extensión de
  descarga, trazado de ruta verificada) directamente sobre el mapa, y
  captura de `acimut_grados` por fusión de sensores.

Ver el detalle completo de fases en `mobile/ESPECIFICACION_MOVIL_OFFLINE.md`.
