# SGAIE Móvil — Android (scaffold M1+M2)

Proyecto Android nativo del componente móvil descrito en
`mobile/ESPECIFICACION_MOVIL_OFFLINE.md`. Este scaffold cubre las fases
**M1** (mapa offline con MapLibre, empaquetado de tiles vía MBTiles) y
**M2** (extracción ArcGIS → GeoPackage, visualización de capas) del
roadmap (§12). M3+ (edición offline, fotos, cola de sincronización,
`applyEdits`) sigue fuera de alcance.

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

## Próximos pasos (fuera de alcance de M1+M2)

- M3+: CRUD de postes/redes/equipos en campo, notas de
  incumplimiento/aceptación de ruta, fotos geolocalizadas, cola de
  sincronización (`cola_sincronizacion`) y sync de vuelta a ArcGIS
  (`applyEdits`/`synchronizeReplica`).

Ver el detalle completo de fases en `mobile/ESPECIFICACION_MOVIL_OFFLINE.md`.
