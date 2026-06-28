# SGAIE Móvil — Android (scaffold M1+M2+M3)

Proyecto Android nativo del componente móvil descrito en
`mobile/ESPECIFICACION_MOVIL_OFFLINE.md`. Este scaffold cubre las fases
**M1** (mapa offline con MapLibre, empaquetado de tiles vía MBTiles),
**M2** (extracción ArcGIS → GeoPackage, visualización de capas) y **M3**
(CRUD offline de postes/redes/equipos, notas de incumplimiento y de
aceptación de ruta, cola de sincronización) del roadmap (§12). M4+ (fotos
con geolocalización ya enlazadas a sync real, `applyEdits`/
`synchronizeReplica` contra ArcGIS) sigue fuera de alcance.

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

## Próximos pasos (fuera de alcance de M1+M2+M3)

- M4+: fotos geolocalizadas adjuntas a notas/entidades, worker que drena
  `cola_sincronizacion` y sincroniza de vuelta a ArcGIS
  (`applyEdits`/`synchronizeReplica`), resolución de conflictos, dibujo
  interactivo de geometrías (extensión de descarga, trazado de ruta
  verificada) directamente sobre el mapa.

Ver el detalle completo de fases en `mobile/ESPECIFICACION_MOVIL_OFFLINE.md`.
