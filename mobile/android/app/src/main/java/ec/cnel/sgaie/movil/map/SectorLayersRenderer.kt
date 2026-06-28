package ec.cnel.sgaie.movil.map

import android.content.Context
import android.graphics.Color
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacion
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacionRepository
import ec.cnel.sgaie.movil.data.Poste
import ec.cnel.sgaie.movil.data.PosteRepository
import ec.cnel.sgaie.movil.data.TramoRed
import ec.cnel.sgaie.movil.data.TramoRedRepository
import org.json.JSONArray
import org.json.JSONObject
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.Style
import org.maplibre.android.style.expressions.Expression
import org.maplibre.android.style.layers.CircleLayer
import org.maplibre.android.style.layers.LineLayer
import org.maplibre.android.style.layers.PropertyFactory
import org.maplibre.android.style.sources.GeoJsonSource

/**
 * Dibuja, sobre el estilo ya cargado del mapa offline, las capas vectoriales
 * de un sector de trabajo (postes, tramos de red, equipos) leídas
 * directamente del GeoPackage local (§6: "capas superpuestas ... se dibujan
 * directamente desde el GeoPackage local").
 *
 * Los equipos no tienen `sector_trabajo_id` propio (§4.4: heredan ubicación
 * de `poste_id`), así que se obtienen recorriendo los equipos de cada poste
 * del sector; un equipo sin poste asignado no es asociable a un sector y
 * queda fuera de esta vista hasta que se confirme un mecanismo distinto.
 */
object SectorLayersRenderer {

    private const val SOURCE_POSTE = "sgaie-postes-source"
    private const val LAYER_POSTE = "sgaie-postes-layer"
    private const val SOURCE_TRAMO_RED = "sgaie-tramos-red-source"
    private const val LAYER_TRAMO_RED = "sgaie-tramos-red-layer"
    private const val SOURCE_EQUIPO = "sgaie-equipos-source"
    private const val LAYER_EQUIPO = "sgaie-equipos-layer"

    private const val PROP_ESTADO_FISICO = "estado_fisico"
    private const val PROP_TIPO_RED = "tipo_red"

    /** Agrega (o refresca, si ya existían) las capas del sector [sectorTrabajoId] sobre [mapa]. */
    fun agregarCapasDeSector(mapa: MapLibreMap, context: Context, sectorTrabajoId: Long) {
        val estilo = mapa.style ?: return

        val postes = PosteRepository(context).listarPorSector(sectorTrabajoId)
        val tramos = TramoRedRepository(context).listarPorSector(sectorTrabajoId)
        val equipoRepository = EquipoTelecomunicacionRepository(context)
        val equipos = postes.flatMap { equipoRepository.listarPorPoste(it.id) }

        agregarOActualizarFuente(estilo, SOURCE_TRAMO_RED, geoJsonDeTramos(tramos))
        agregarOActualizarFuente(estilo, SOURCE_EQUIPO, geoJsonDeEquipos(equipos))
        agregarOActualizarFuente(estilo, SOURCE_POSTE, geoJsonDePostes(postes))

        if (estilo.getLayer(LAYER_TRAMO_RED) == null) estilo.addLayer(capaTramos())
        if (estilo.getLayer(LAYER_EQUIPO) == null) estilo.addLayer(capaEquipos())
        if (estilo.getLayer(LAYER_POSTE) == null) estilo.addLayer(capaPostes())
    }

    private fun agregarOActualizarFuente(estilo: Style, sourceId: String, geoJson: String) {
        val fuenteExistente = estilo.getSourceAs<GeoJsonSource>(sourceId)
        if (fuenteExistente != null) {
            fuenteExistente.setGeoJson(geoJson)
        } else {
            estilo.addSource(GeoJsonSource(sourceId, geoJson))
        }
    }

    private fun geoJsonDePostes(postes: List<Poste>): String {
        val features = JSONArray()
        postes.forEach { poste ->
            val geometria = JSONObject()
                .put("type", "Point")
                .put("coordinates", JSONArray().put(poste.geometria.x).put(poste.geometria.y))
            val propiedades = JSONObject()
                .put("id", poste.id)
                .put("codigo_poste", poste.codigoPoste)
                .put("tipo_poste", poste.tipoPoste.name)
                .put(PROP_ESTADO_FISICO, poste.estadoFisico.name)
            features.put(JSONObject().put("type", "Feature").put("geometry", geometria).put("properties", propiedades))
        }
        return JSONObject().put("type", "FeatureCollection").put("features", features).toString()
    }

    private fun geoJsonDeTramos(tramos: List<TramoRed>): String {
        val features = JSONArray()
        tramos.forEach { tramo ->
            val coordenadas = JSONArray()
            tramo.geometria.points.forEach { punto -> coordenadas.put(JSONArray().put(punto.x).put(punto.y)) }
            val geometria = JSONObject().put("type", "LineString").put("coordinates", coordenadas)
            val propiedades = JSONObject()
                .put("id", tramo.id)
                .put(PROP_TIPO_RED, tramo.tipoRed.name)
                .put("estado", tramo.estado.name)
            features.put(JSONObject().put("type", "Feature").put("geometry", geometria).put("properties", propiedades))
        }
        return JSONObject().put("type", "FeatureCollection").put("features", features).toString()
    }

    private fun geoJsonDeEquipos(equipos: List<EquipoTelecomunicacion>): String {
        val features = JSONArray()
        equipos.forEach { equipo ->
            val geometria = equipo.geometria ?: return@forEach
            val geometriaJson = JSONObject()
                .put("type", "Point")
                .put("coordinates", JSONArray().put(geometria.x).put(geometria.y))
            val propiedades = JSONObject()
                .put("id", equipo.id)
                .put("tipo_equipo", equipo.tipoEquipo.name)
                .put("estado", equipo.estado.name)
            features.put(
                JSONObject().put("type", "Feature").put("geometry", geometriaJson).put("properties", propiedades),
            )
        }
        return JSONObject().put("type", "FeatureCollection").put("features", features).toString()
    }

    private fun capaPostes(): CircleLayer = CircleLayer(LAYER_POSTE, SOURCE_POSTE).withProperties(
        PropertyFactory.circleRadius(6f),
        PropertyFactory.circleStrokeWidth(1.5f),
        PropertyFactory.circleStrokeColor(Color.WHITE),
        PropertyFactory.circleColor(
            Expression.match(
                Expression.get(PROP_ESTADO_FISICO),
                Expression.color(Color.parseColor("#757575")),
                Expression.stop("BUENO", Expression.color(Color.parseColor("#2e7d32"))),
                Expression.stop("REGULAR", Expression.color(Color.parseColor("#f9a825"))),
                Expression.stop("MALO", Expression.color(Color.parseColor("#d32f2f"))),
                Expression.stop("RETIRADO", Expression.color(Color.parseColor("#757575"))),
            ),
        ),
    )

    private fun capaTramos(): LineLayer = LineLayer(LAYER_TRAMO_RED, SOURCE_TRAMO_RED).withProperties(
        PropertyFactory.lineWidth(3f),
        PropertyFactory.lineColor(
            Expression.match(
                Expression.get(PROP_TIPO_RED),
                Expression.color(Color.parseColor("#616161")),
                Expression.stop("FIBRA_OPTICA", Expression.color(Color.parseColor("#1565c0"))),
                Expression.stop("COAXIAL", Expression.color(Color.parseColor("#6a1b9a"))),
                Expression.stop("ELECTRICA", Expression.color(Color.parseColor("#e65100"))),
                Expression.stop("OTRO", Expression.color(Color.parseColor("#616161"))),
            ),
        ),
    )

    private fun capaEquipos(): CircleLayer = CircleLayer(LAYER_EQUIPO, SOURCE_EQUIPO).withProperties(
        PropertyFactory.circleRadius(4f),
        PropertyFactory.circleStrokeWidth(1f),
        PropertyFactory.circleStrokeColor(Color.BLACK),
        PropertyFactory.circleColor(Color.parseColor("#00897b")),
    )
}
