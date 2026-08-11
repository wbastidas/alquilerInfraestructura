package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.sf.GeometryType
import org.json.JSONObject
import java.time.Instant

/**
 * Dominio §4.7: fotografía geolocalizada vinculada a cualquier entidad de
 * campo (poste/tramo/equipo/nota), mismo patrón que `FotografiaNovedad` del
 * backend. La geometría (punto) se puebla con `latitud`/`longitud` para que
 * la fotografía sea igualmente visualizable en capas futuras del mapa.
 */
data class Fotografia(
    val id: Long = 0,
    val globalId: String,
    val entidadTipo: EntidadTipo,
    val entidadId: Long,
    val rutaArchivoLocal: String,
    val latitud: Double,
    val longitud: Double,
    val altitudM: Double? = null,
    val precisionGpsM: Double? = null,
    val acimutGrados: Double? = null,
    val timestampCaptura: Instant = Instant.now(),
    val hashSha256: String,
    val sincronizada: Boolean = false,
    val operacionPendiente: OperacionPendiente = OperacionPendiente.CREAR,
)

private const val COL_ENTIDAD_TIPO = "entidad_tipo"
private const val COL_ENTIDAD_ID = "entidad_id"
private const val COL_RUTA_ARCHIVO_LOCAL = "ruta_archivo_local"
private const val COL_ALTITUD_M = "altitud_m"
private const val COL_PRECISION_GPS_M = "precision_gps_m"
private const val COL_ACIMUT_GRADOS = "acimut_grados"
private const val COL_TIMESTAMP_CAPTURA = "timestamp_captura"
private const val COL_HASH_SHA256 = "hash_sha256"
private const val COL_SINCRONIZADA = "sincronizada"

class FotografiaRepository(private val context: Context) {

    private val colaSincronizacion = ColaSincronizacionRepository(context)

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_FOTOGRAFIA,
            tipoGeometria = GeometryType.POINT,
            geometriaOpcional = true,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(GeoPackageContract.COL_GLOBAL_ID, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ENTIDAD_TIPO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ENTIDAD_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_RUTA_ARCHIVO_LOCAL, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ALTITUD_M, GeoPackageDataType.DOUBLE),
                FeatureColumn.createColumn(COL_PRECISION_GPS_M, GeoPackageDataType.DOUBLE),
                FeatureColumn.createColumn(COL_ACIMUT_GRADOS, GeoPackageDataType.DOUBLE),
                FeatureColumn.createColumn(COL_TIMESTAMP_CAPTURA, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_HASH_SHA256, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_SINCRONIZADA, GeoPackageDataType.BOOLEAN),
                FeatureColumn.createColumn(GeoPackageContract.COL_OPERACION_PENDIENTE, GeoPackageDataType.TEXT),
            ),
        )
    }

    /** Inserta la fotografía y la encola en `cola_sincronizacion` (§5.3: se sube como adjunto de su entidad relacionada). */
    fun insertar(foto: Fotografia): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_FOTOGRAFIA)
        val fila = dao.newRow()
        fila.geometry = GeoPackageProvider.geometriaPuntoWgs84(foto.longitud, foto.latitud)
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, foto.globalId)
        fila.setValue(COL_ENTIDAD_TIPO, foto.entidadTipo.name)
        fila.setValue(COL_ENTIDAD_ID, foto.entidadId)
        fila.setValue(COL_RUTA_ARCHIVO_LOCAL, foto.rutaArchivoLocal)
        fila.setValue(COL_ALTITUD_M, foto.altitudM)
        fila.setValue(COL_PRECISION_GPS_M, foto.precisionGpsM)
        fila.setValue(COL_ACIMUT_GRADOS, foto.acimutGrados)
        fila.setValue(COL_TIMESTAMP_CAPTURA, foto.timestampCaptura.toString())
        fila.setValue(COL_HASH_SHA256, foto.hashSha256)
        fila.setValue(COL_SINCRONIZADA, foto.sincronizada)
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, OperacionPendiente.CREAR.name)
        val idLocal = dao.create(fila)

        colaSincronizacion.encolar(
            tablaOrigen = TablaOrigen.FOTOGRAFIA,
            entidadTipo = foto.entidadTipo,
            entidadId = idLocal,
            operacion = OperacionSincronizacion.CREAR,
            payloadJson = payloadJson(foto.copy(id = idLocal)),
        )
        return idLocal
    }

    fun listarPorEntidad(entidadTipo: EntidadTipo, entidadId: Long): List<Fotografia> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_FOTOGRAFIA)
        val resultado = mutableListOf<Fotografia>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                if (EntidadTipo.valueOf(fila.getValue(COL_ENTIDAD_TIPO) as String) != entidadTipo) continue
                if ((fila.getValue(COL_ENTIDAD_ID) as Number).toLong() != entidadId) continue
                val punto = fila.geometry?.geometry as mil.nga.sf.Point?
                resultado += Fotografia(
                    id = fila.id,
                    globalId = fila.getValue(GeoPackageContract.COL_GLOBAL_ID) as String,
                    entidadTipo = entidadTipo,
                    entidadId = entidadId,
                    rutaArchivoLocal = fila.getValue(COL_RUTA_ARCHIVO_LOCAL) as String,
                    latitud = punto?.y ?: 0.0,
                    longitud = punto?.x ?: 0.0,
                    altitudM = fila.getValue(COL_ALTITUD_M) as Double?,
                    precisionGpsM = fila.getValue(COL_PRECISION_GPS_M) as Double?,
                    acimutGrados = fila.getValue(COL_ACIMUT_GRADOS) as Double?,
                    timestampCaptura = Instant.parse(fila.getValue(COL_TIMESTAMP_CAPTURA) as String),
                    hashSha256 = fila.getValue(COL_HASH_SHA256) as String,
                    sincronizada = fila.getValue(COL_SINCRONIZADA) as Boolean,
                    operacionPendiente = OperacionPendiente.valueOf(
                        fila.getValue(GeoPackageContract.COL_OPERACION_PENDIENTE) as String,
                    ),
                )
            }
        }
        return resultado
    }

    private fun payloadJson(foto: Fotografia): String = JSONObject().apply {
        put("id", foto.id)
        put("global_id", foto.globalId)
        put("entidad_tipo", foto.entidadTipo.name)
        put("entidad_id", foto.entidadId)
        put("ruta_archivo_local", foto.rutaArchivoLocal)
        put("latitud", foto.latitud)
        put("longitud", foto.longitud)
        put("altitud_m", foto.altitudM)
        put("precision_gps_m", foto.precisionGpsM)
        put("acimut_grados", foto.acimutGrados)
        put("timestamp_captura", foto.timestampCaptura.toString())
        put("hash_sha256", foto.hashSha256)
    }.toString()
}
