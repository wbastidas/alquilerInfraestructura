package ec.cnel.sgaie.movil.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Validaciones de entrada de [ArcGisRestClient] que protegen el token y la
 * consulta al Feature Service. Ninguna de ellas llega a la red: fallan antes
 * de construir la petición, por lo que son verificables en la JVM.
 */
class ArcGisRestClientTest {

    private val tokenDePrueba = ArcGisTokenProvider { "token-ficticio" }

    @Test
    fun `rechaza una URL de Feature Service sin TLS`() {
        val excepcion = assertThrows(IllegalArgumentException::class.java) {
            ArcGisRestClient("http://servidor.interno/arcgis/rest/services/X/FeatureServer", tokenDePrueba)
        }
        assertTrue(excepcion.message!!.contains("https://"))
    }

    @Test
    fun `rechaza una URL que no es http en absoluto`() {
        assertThrows(IllegalArgumentException::class.java) {
            ArcGisRestClient("ftp://servidor/FeatureServer", tokenDePrueba)
        }
    }

    @Test
    fun `acepta una URL https`() {
        val cliente = ArcGisRestClient(
            "https://services.arcgis.com/org/arcgis/rest/services/SGAIE/FeatureServer",
            tokenDePrueba,
        )
        assertTrue(cliente is ArcGisRestClient)
    }

    @Test
    fun `rechaza un GlobalID con comillas que podria alterar la clausula where`() {
        val cliente = ArcGisRestClient("https://servicio.example/FeatureServer", tokenDePrueba)
        assertThrows(IllegalArgumentException::class.java) {
            cliente.obtenerObjectIdPorGlobalId(0, "' OR 1=1 --")
        }
    }

    @Test
    fun `rechaza un GlobalID con espacios o caracteres fuera del alfabeto de un GUID`() {
        val cliente = ArcGisRestClient("https://servicio.example/FeatureServer", tokenDePrueba)
        for (invalido in listOf("abc def", "abc;drop", "", "id_con_guion_bajo")) {
            assertThrows(IllegalArgumentException::class.java) {
                cliente.obtenerObjectIdPorGlobalId(0, invalido)
            }
        }
    }

    @Test
    fun `el envelope se serializa con el formato de geometria de ArcGIS`() {
        val json = Envelope(xmin = -80.0, ymin = -2.5, xmax = -79.5, ymax = -2.0).aJsonEsri()

        assertTrue(json.contains("\"xmin\":-80"))
        assertTrue(json.contains("\"ymax\":-2"))
        assertTrue(json.contains("\"spatialReference\""))
        assertTrue(json.contains("\"wkid\":4326"))
    }

    @Test
    fun `el envelope respeta un wkid distinto del predeterminado`() {
        val json = Envelope(0.0, 0.0, 1.0, 1.0, wkid = 3857).aJsonEsri()
        assertTrue(json.contains("\"wkid\":3857"))
    }

    @Test
    fun `las capas configuradas mantienen el orden esperado del Feature Service`() {
        assertEquals(0, ArcGisConfig.Capas.POSTE)
        assertEquals(1, ArcGisConfig.Capas.TRAMO_RED)
        assertEquals(2, ArcGisConfig.Capas.EQUIPO_TELECOMUNICACION)
    }
}
