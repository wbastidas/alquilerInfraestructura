package ec.cnel.sgaie.movil.sync

import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.io.File
import java.io.IOException

/**
 * Cliente REST mínimo hacia un Feature Service de ArcGIS "sync enabled"
 * (§5.1/§5.3). Implementa solo `createReplica` con `dataFormat=sqlite`
 * (la réplica resultante es en sí misma un archivo SQLite, que
 * [ReplicaGeodatabaseReader] puede abrir directamente sin parsers
 * adicionales).
 *
 * `synchronizeReplica`/`applyEdits` (subida de cambios, §5.3) y `addAttachment`
 * (fotos, §5.3/M4) quedan fuera de alcance de M2 (extracción), que solo
 * cubre el sentido ArcGIS -> dispositivo.
 *
 * Simplificado a flujo síncrono (`async=false`); para sectores grandes
 * ArcGIS puede forzar un job asíncrono — `# TODO: agregar polling de
 * /createReplica/jobs/{jobId} si CNEL EP confirma sectores grandes (§13)`.
 */
class ArcGisRestClient(
    private val featureServiceUrl: String,
    private val tokenProvider: ArcGisTokenProvider,
    private val httpClient: OkHttpClient = OkHttpClient(),
) {

    /**
     * Solicita una réplica del Feature Service filtrada por [envelope] para las [capas]
     * indicadas, y descarga el `.geodatabase` (SQLite) resultante a [destino].
     */
    fun createReplica(
        nombreReplica: String,
        capas: List<Int>,
        envelope: Envelope,
        destino: File,
    ): File {
        val body = FormBody.Builder()
            .add("f", "json")
            .add("token", tokenProvider.obtenerToken())
            .add("replicaName", nombreReplica)
            .add("layers", capas.joinToString(","))
            .add("geometry", envelope.aJsonEsri())
            .add("geometryType", "esriGeometryEnvelope")
            .add("inSR", envelope.wkid.toString())
            .add("transportType", "esriTransportTypeUrl")
            .add("returnAttachments", "false")
            .add("syncModel", "perLayer")
            .add("dataFormat", "sqlite")
            .add("async", "false")
            .build()

        val request = Request.Builder()
            .url("$featureServiceUrl/createReplica")
            .post(body)
            .build()

        val respuestaJson = httpClient.newCall(request).execute().use { respuesta ->
            if (!respuesta.isSuccessful) {
                throw IOException("createReplica falló con código ${respuesta.code}")
            }
            JSONObject(respuesta.body?.string().orEmpty())
        }

        if (respuestaJson.has("error")) {
            val error = respuestaJson.getJSONObject("error")
            throw IOException("createReplica devolvió error: ${error.optString("message")}")
        }

        val urlDescarga = respuestaJson.optString("URL").ifEmpty {
            throw IOException("Respuesta de createReplica sin campo URL: $respuestaJson")
        }

        descargarArchivo(urlDescarga, destino)
        return destino
    }

    private fun descargarArchivo(url: String, destino: File) {
        val request = Request.Builder().url(url).get().build()
        httpClient.newCall(request).execute().use { respuesta ->
            if (!respuesta.isSuccessful) {
                throw IOException("Descarga de réplica falló con código ${respuesta.code}")
            }
            destino.outputStream().use { salida ->
                respuesta.body?.byteStream()?.copyTo(salida)
                    ?: throw IOException("Respuesta de descarga sin cuerpo")
            }
        }
    }
}
