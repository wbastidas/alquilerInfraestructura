package ec.cnel.sgaie.movil.sync

import org.json.JSONObject

/** Filtro geográfico (rectángulo WGS84) para `createReplica`, §5.1: "extensión geográfica dibujada en el mapa". */
data class Envelope(
    val xmin: Double,
    val ymin: Double,
    val xmax: Double,
    val ymax: Double,
    val wkid: Int = 4326,
) {
    fun aJsonEsri(): String = JSONObject()
        .put("xmin", xmin)
        .put("ymin", ymin)
        .put("xmax", xmax)
        .put("ymax", ymax)
        .put("spatialReference", JSONObject().put("wkid", wkid))
        .toString()
}
