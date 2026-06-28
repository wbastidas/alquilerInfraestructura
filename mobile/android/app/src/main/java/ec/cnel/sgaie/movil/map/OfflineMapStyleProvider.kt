package ec.cnel.sgaie.movil.map

import org.maplibre.android.style.layers.RasterLayer
import org.maplibre.android.style.sources.RasterSource
import org.maplibre.android.style.sources.TileSet

/**
 * Construye un estilo MapLibre mínimo (sin acceso a Internet) a partir de la
 * plantilla de tiles servida localmente por [OfflineTileServer]. No depende
 * de ningún estilo remoto (Mapbox/MapTiler/etc.): es la base del mapa
 * offline open-source descrito en mobile/ESPECIFICACION_MOVIL_OFFLINE.md §7.
 */
object OfflineMapStyleProvider {

    private const val SOURCE_ID = "sector-offline-source"
    private const val LAYER_ID = "sector-offline-layer"
    private const val TILE_SIZE = 256

    fun construirEstiloJson(tileUrlTemplate: String): String {
        return """
            {
              "version": 8,
              "sources": {
                "$SOURCE_ID": {
                  "type": "raster",
                  "tiles": ["$tileUrlTemplate"],
                  "tileSize": $TILE_SIZE
                }
              },
              "layers": [
                {
                  "id": "$LAYER_ID",
                  "type": "raster",
                  "source": "$SOURCE_ID"
                }
              ]
            }
        """.trimIndent()
    }

    fun construirTileSet(tileUrlTemplate: String): TileSet =
        TileSet("2.1.0", tileUrlTemplate).apply { tileSize = TILE_SIZE }

    fun construirRasterSource(tileUrlTemplate: String): RasterSource =
        RasterSource(SOURCE_ID, construirTileSet(tileUrlTemplate), TILE_SIZE)

    fun construirRasterLayer(): RasterLayer = RasterLayer(LAYER_ID, SOURCE_ID)
}
