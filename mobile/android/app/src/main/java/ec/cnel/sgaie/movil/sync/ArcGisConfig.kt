package ec.cnel.sgaie.movil.sync

/**
 * Configuración de conexión a los Feature Services "sync enabled" de ArcGIS
 * de CNEL EP (mobile/ESPECIFICACION_MOVIL_OFFLINE.md §3.2/§5.1).
 *
 * `# TODO: confirmar con CNEL EP la URL real del/los Feature Service(s) de
 * origen y si ya tienen sync habilitado (isDataVersioned/syncEnabled) — sin
 * esto, createReplica/synchronizeReplica no son utilizables (§13).`
 */
object ArcGisConfig {
    const val FEATURE_SERVICE_URL_PLACEHOLDER =
        "https://services.arcgis.com/<org-id>/arcgis/rest/services/<servicio>/FeatureServer"

    /** Identificadores de capa dentro del Feature Service, uno por entidad de red (§4.2-§4.4). */
    object Capas {
        const val POSTE = 0
        const val TRAMO_RED = 1
        const val EQUIPO_TELECOMUNICACION = 2
    }
}

/** Provee el token OAuth2 de la organización ArcGIS de CNEL EP (§9). */
fun interface ArcGisTokenProvider {
    fun obtenerToken(): String
}
