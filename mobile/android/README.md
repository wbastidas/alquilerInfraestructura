# SGAIE Móvil — Android (scaffold M1)

Proyecto Android nativo del componente móvil descrito en
`mobile/ESPECIFICACION_MOVIL_OFFLINE.md`. Este scaffold corresponde a la
**Fase M1** del roadmap (§ tabla de fases): mapa offline con MapLibre,
empaquetado de tiles vía MBTiles, **sin** integración con ArcGIS todavía
(eso es M2+).

## Qué incluye este scaffold

- Proyecto Gradle (Kotlin DSL) con un único módulo `:app`.
- Jetpack Compose + Material 3 (UI mínima).
- `MapView` de MapLibre embebido en Compose (`map/OfflineMapScreen.kt`),
  estilo construido en memoria (`map/OfflineMapStyleProvider.kt`, sin
  estilos remotos de terceros).
- Servidor HTTP embebido (`map/OfflineTileServer.kt`, NanoHTTPD) que sirve
  un archivo `.mbtiles` local como tiles XYZ en `127.0.0.1`, con la
  conversión de fila TMS→XYZ que requiere el formato MBTiles.
- Sin `INTERNET` en el manifiesto: el mapa funciona 100% offline a partir
  de un paquete de tiles ya copiado al dispositivo.

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

## Próximos pasos (fuera de alcance de M1)

- M2: extracción de sectores desde ArcGIS (`createReplica`) y carga del
  modelo de datos en GeoPackage local.
- M3+: CRUD de postes/redes/equipos, notas de incumplimiento/aceptación
  de ruta, fotos geolocalizadas, cola de sincronización
  (`cola_sincronizacion`) y sync de vuelta a ArcGIS (`applyEdits`).

Ver el detalle completo de fases en `mobile/ESPECIFICACION_MOVIL_OFFLINE.md`.
