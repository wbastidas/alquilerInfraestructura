package ec.cnel.sgaie.movil.map

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * El estilo del mapa offline (§7) se construye en memoria y no debe apuntar a
 * ningún servicio remoto de terceros: los tiles salen del servidor local que
 * expone el .mbtiles del sector descargado.
 */
class OfflineMapStyleProviderTest {

    private val plantillaLocal = "http://127.0.0.1:8081/tiles/{z}/{x}/{y}.png"

    @Test
    fun `el estilo incluye la fuente raster con la plantilla de tiles local`() {
        val estilo = OfflineMapStyleProvider.construirEstiloJson(plantillaLocal)

        assertTrue(estilo.contains("\"version\": 8"))
        assertTrue(estilo.contains("\"type\": \"raster\""))
        assertTrue(estilo.contains(plantillaLocal))
        assertTrue(estilo.contains("\"tileSize\": 256"))
    }

    @Test
    fun `el estilo no referencia proveedores remotos de mapas`() {
        val estilo = OfflineMapStyleProvider.construirEstiloJson(plantillaLocal)

        for (proveedor in listOf("mapbox", "maptiler", "openstreetmap", "google", "arcgisonline")) {
            assertFalse(
                "El mapa debe ser 100% offline; apareció $proveedor en el estilo",
                estilo.lowercase().contains(proveedor),
            )
        }
        assertFalse(estilo.contains("https://"))
    }

    @Test
    fun `la capa declarada usa la fuente declarada`() {
        val estilo = OfflineMapStyleProvider.construirEstiloJson(plantillaLocal)
        val idFuente = Regex("\"sources\"\\s*:\\s*\\{\\s*\"([^\"]+)\"").find(estilo)!!.groupValues[1]

        assertTrue(estilo.contains("\"source\": \"$idFuente\""))
    }
}
