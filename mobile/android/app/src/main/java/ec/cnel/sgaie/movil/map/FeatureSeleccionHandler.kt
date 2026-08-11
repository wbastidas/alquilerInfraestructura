package ec.cnel.sgaie.movil.map

import ec.cnel.sgaie.movil.data.EntidadTipo
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapLibreMap

/** Entidad de red identificada por un tap del usuario sobre el mapa (M3, §5.2: edición offline). */
data class FeatureSeleccionada(val entidadTipo: EntidadTipo, val entidadId: Long)

/**
 * Resuelve qué poste/tramo/equipo (entre las capas dibujadas por
 * [SectorLayersRenderer]) está bajo el punto tocado, usando la API de
 * consulta de features renderizados de MapLibre.
 *
 * Se consulta una capa a la vez, en orden de prioridad visual (equipo/poste,
 * que son puntos pequeños, antes que tramo, una línea con un objetivo táctil
 * más amplio), porque `queryRenderedFeatures` no informa a qué capa
 * pertenece cada resultado cuando se pasan varias a la vez.
 */
object FeatureSeleccionHandler {

    private val ordenPrioridadTap = listOf(
        SectorLayersRenderer.LAYER_EQUIPO,
        SectorLayersRenderer.LAYER_POSTE,
        SectorLayersRenderer.LAYER_TRAMO_RED,
    )

    fun seleccionarEn(mapa: MapLibreMap, puntoTocado: LatLng): FeatureSeleccionada? {
        val puntoPantalla = mapa.projection.toScreenLocation(puntoTocado)
        for (layerId in ordenPrioridadTap) {
            val entidadTipo = SectorLayersRenderer.entidadTipoDeCapa(layerId) ?: continue
            val feature = mapa.queryRenderedFeatures(puntoPantalla, layerId).firstOrNull() ?: continue
            val entidadId = feature.getProperty("id")?.asLong ?: continue
            return FeatureSeleccionada(entidadTipo, entidadId)
        }
        return null
    }
}
