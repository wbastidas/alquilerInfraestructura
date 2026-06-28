// Build script raíz del componente móvil SGAIE (mobile/ESPECIFICACION_MOVIL_OFFLINE.md).
// Solo declara y resuelve versiones de plugins; cada módulo (hoy solo :app)
// los aplica según necesite.
plugins {
    id("com.android.application") version "8.6.1" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
}
