package ec.cnel.sgaie.movil.sync

import kotlinx.coroutines.sync.Mutex

/**
 * Exclusión mutua para que extracción (`createReplica`, §5.1) y subida de
 * cambios (`applyEdits`/`addAttachment`, §5.3) nunca corran en simultáneo
 * dentro del mismo dispositivo —disparadas manualmente desde
 * [ec.cnel.sgaie.movil.map.DescargaSectorScreen]/
 * [ec.cnel.sgaie.movil.map.SincronizacionScreen], o en segundo plano por
 * [SincronizacionWorker]—, ya que ambas leen/escriben el mismo GeoPackage
 * local y `geopackage-android` no garantiza seguridad ante escrituras
 * concurrentes desde dos hilos (§13, no verificado en este sandbox).
 *
 * `# NOTA: esto NO es la solución a la concurrencia ENTRE dispositivos
 * distintos (varios técnicos de campo sincronizando a la vez): cada
 * dispositivo ya tiene su propio GeoPackage y su propia
 * cola_sincronizacion (outbox, §4.9) totalmente independientes entre sí, y
 * llaman directamente a la REST API de ArcGIS —diseñada para atender
 * múltiples clientes concurrentes—. El único punto de contención real
 * entre dispositivos es el Feature Service de ArcGIS, que serializa sus
 * propias escrituras a nivel de base de datos del lado del servidor; esa
 * parte queda fuera del alcance de esta app. El único caso cruzado que la
 * app sí debe resolver —dos dispositivos editando el mismo elemento— ya lo
 * cubre la resolución de conflictos de §5.4 (ConflictoSincronizacionRepository).`
 */
object SincronizacionLock {
    val mutex = Mutex()
}
