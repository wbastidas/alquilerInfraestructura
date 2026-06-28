package ec.cnel.sgaie.movil.sync

import okhttp3.FormBody
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException

/**
 * Cliente REST mínimo hacia un Feature Service de ArcGIS "sync enabled"
 * (§5.1/§5.3). Implementa `createReplica` (extracción, M2) y, desde M5,
 * `applyEdits`/`addAttachment` (subida de cambios, §5.3).
 *
 * `synchronizeReplica` (alternativa "réplica completa" a `applyEdits` para
 * subir cambios) queda fuera de alcance: `applyEdits` por capa es la opción
 * más simple y suficiente dado que el outbox (`cola_sincronizacion`) ya
 * encola cambios por entidad individual, no por snapshot completo de réplica.
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

    /**
     * Sube altas/ediciones/bajas a la capa [layerId] (§5.3). Usa
     * `useGlobalIds=true` para que [updates]/[deletes] identifiquen cada
     * feature por su `global_id` (el único identificador estable que el
     * dispositivo conoce sin depender de un OBJECTID asignado por el
     * servidor) en vez de requerir una resolución previa de OBJECTID.
     *
     * `# NOTA: requiere que la capa tenga supportsApplyEditsWithGlobalIds=true
     * en su definición de servicio; no se pudo confirmar contra un Feature
     * Service real de CNEL EP en este sandbox (§13). Si la capa no lo
     * soporta, ArcGIS devuelve error y el ítem queda en ERROR para revisión
     * manual (nunca se aplica con datos incorrectos).`
     *
     * Devuelve el JSON de respuesta crudo (`addResults`/`updateResults`/
     * `deleteResults`, cada uno con `globalId`, `success` y, si falla,
     * `error.code`/`error.description`) para que el llamador decida
     * ENVIADO/ERROR/CONFLICTO por feature.
     */
    fun applyEdits(
        layerId: Int,
        adds: List<JSONObject> = emptyList(),
        updates: List<JSONObject> = emptyList(),
        deletes: List<String> = emptyList(),
    ): JSONObject {
        val body = FormBody.Builder()
            .add("f", "json")
            .add("token", tokenProvider.obtenerToken())
            .add("useGlobalIds", "true")
            .add("adds", JSONArray(adds).toString())
            .add("updates", JSONArray(updates).toString())
            .add("deletes", deletes.joinToString(","))
            .add("rollbackOnFailure", "false")
            .build()

        val request = Request.Builder()
            .url("$featureServiceUrl/$layerId/applyEdits")
            .post(body)
            .build()

        val respuestaJson = httpClient.newCall(request).execute().use { respuesta ->
            if (!respuesta.isSuccessful) {
                throw IOException("applyEdits (capa $layerId) falló con código ${respuesta.code}")
            }
            JSONObject(respuesta.body?.string().orEmpty())
        }

        if (respuestaJson.has("error")) {
            val error = respuestaJson.getJSONObject("error")
            throw IOException("applyEdits devolvió error: ${error.optString("message")}")
        }
        return respuestaJson
    }

    /**
     * Resuelve el OBJECTID asignado por el servidor a partir del [globalId]
     * local. Necesario únicamente para `addAttachment` (§5.3/M4), cuyo
     * endpoint REST estándar de ArcGIS identifica la feature por OBJECTID y
     * no admite `useGlobalIds` como `applyEdits`.
     */
    fun obtenerObjectIdPorGlobalId(layerId: Int, globalId: String): Long? {
        val url = "$featureServiceUrl/$layerId/query".toHttpUrl().newBuilder()
            .addQueryParameter("f", "json")
            .addQueryParameter("token", tokenProvider.obtenerToken())
            .addQueryParameter("where", "GlobalID = '$globalId'")
            .addQueryParameter("outFields", "OBJECTID")
            .addQueryParameter("returnGeometry", "false")
            .build()

        val request = Request.Builder().url(url).get().build()
        val respuestaJson = httpClient.newCall(request).execute().use { respuesta ->
            if (!respuesta.isSuccessful) {
                throw IOException("query por globalId (capa $layerId) falló con código ${respuesta.code}")
            }
            JSONObject(respuesta.body?.string().orEmpty())
        }

        if (respuestaJson.has("error")) {
            val error = respuestaJson.getJSONObject("error")
            throw IOException("query por globalId devolvió error: ${error.optString("message")}")
        }

        val features = respuestaJson.optJSONArray("features") ?: return null
        if (features.length() == 0) return null
        return features.getJSONObject(0).getJSONObject("attributes").getLong("OBJECTID")
    }

    /**
     * Sube [archivo] como adjunto de la feature [objectId] de la capa
     * [layerId] (§5.3/M4: fotos vinculadas a poste/tramo_red/equipo).
     */
    fun addAttachment(layerId: Int, objectId: Long, archivo: File): JSONObject {
        val mediaType = "image/jpeg".toMediaType()
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("f", "json")
            .addFormDataPart("token", tokenProvider.obtenerToken())
            .addFormDataPart("attachment", archivo.name, archivo.asRequestBody(mediaType))
            .build()

        val request = Request.Builder()
            .url("$featureServiceUrl/$layerId/$objectId/addAttachment")
            .post(body)
            .build()

        val respuestaJson = httpClient.newCall(request).execute().use { respuesta ->
            if (!respuesta.isSuccessful) {
                throw IOException("addAttachment (capa $layerId, objectId $objectId) falló con código ${respuesta.code}")
            }
            JSONObject(respuesta.body?.string().orEmpty())
        }

        if (respuestaJson.has("error")) {
            val error = respuestaJson.getJSONObject("error")
            throw IOException("addAttachment devolvió error: ${error.optString("message")}")
        }
        return respuestaJson
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
