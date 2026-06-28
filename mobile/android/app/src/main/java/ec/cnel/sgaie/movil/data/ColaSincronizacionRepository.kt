package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.sf.GeometryType
import java.time.Instant

/**
 * Dominio §4.9: cola de cambios pendientes de subir a ArcGIS (outbox, §5.2).
 * Toda alta/edición/eliminación local de poste/tramo_red/equipo encola aquí
 * un snapshot JSON del registro, que M5 leerá para `synchronizeReplica`/`applyEdits`.
 */
data class ItemColaSincronizacion(
    val id: Long = 0,
    val entidadTipo: EntidadTipo,
    val entidadId: Long,
    val operacion: OperacionSincronizacion,
    val payloadJson: String,
    val intentos: Int = 0,
    val estado: EstadoSincronizacion = EstadoSincronizacion.PENDIENTE,
    val mensajeError: String? = null,
    val creadoEn: Instant = Instant.now(),
)

private const val COL_ENTIDAD_TIPO = "entidad_tipo"
private const val COL_ENTIDAD_ID = "entidad_id"
private const val COL_OPERACION = "operacion"
private const val COL_PAYLOAD_JSON = "payload_json"
private const val COL_INTENTOS = "intentos"
private const val COL_ESTADO = "estado"
private const val COL_MENSAJE_ERROR = "mensaje_error"
private const val COL_CREADO_EN = "creado_en"

/**
 * `cola_sincronizacion` no tiene geometría propia (es metadata de un cambio,
 * no una entidad espacial); se modela igual que `equipo_telecomunicacion`
 * (§4.4, geometría opcional nunca poblada) porque `GeoPackageProvider` solo
 * expone creación de tablas de feature, sin una variante de tabla de
 * atributos puros.
 */
class ColaSincronizacionRepository(private val context: Context) {

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_COLA_SINCRONIZACION,
            tipoGeometria = GeometryType.POINT,
            geometriaOpcional = true,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(COL_ENTIDAD_TIPO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ENTIDAD_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_OPERACION, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_PAYLOAD_JSON, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_INTENTOS, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_ESTADO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_MENSAJE_ERROR, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_CREADO_EN, GeoPackageDataType.TEXT),
            ),
        )
    }

    fun encolar(entidadTipo: EntidadTipo, entidadId: Long, operacion: OperacionSincronizacion, payloadJson: String): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_COLA_SINCRONIZACION)
        val fila = dao.newRow()
        fila.setValue(COL_ENTIDAD_TIPO, entidadTipo.name)
        fila.setValue(COL_ENTIDAD_ID, entidadId)
        fila.setValue(COL_OPERACION, operacion.name)
        fila.setValue(COL_PAYLOAD_JSON, payloadJson)
        fila.setValue(COL_INTENTOS, 0)
        fila.setValue(COL_ESTADO, EstadoSincronizacion.PENDIENTE.name)
        fila.setValue(COL_MENSAJE_ERROR, null)
        fila.setValue(COL_CREADO_EN, Instant.now().toString())
        return dao.create(fila)
    }

    fun listarPendientes(): List<ItemColaSincronizacion> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_COLA_SINCRONIZACION)
        val resultado = mutableListOf<ItemColaSincronizacion>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                if (EstadoSincronizacion.valueOf(fila.getValue(COL_ESTADO) as String) != EstadoSincronizacion.PENDIENTE) continue
                resultado += ItemColaSincronizacion(
                    id = fila.id,
                    entidadTipo = EntidadTipo.valueOf(fila.getValue(COL_ENTIDAD_TIPO) as String),
                    entidadId = (fila.getValue(COL_ENTIDAD_ID) as Number).toLong(),
                    operacion = OperacionSincronizacion.valueOf(fila.getValue(COL_OPERACION) as String),
                    payloadJson = fila.getValue(COL_PAYLOAD_JSON) as String,
                    intentos = (fila.getValue(COL_INTENTOS) as Number).toInt(),
                    estado = EstadoSincronizacion.PENDIENTE,
                    mensajeError = fila.getValue(COL_MENSAJE_ERROR) as String?,
                    creadoEn = Instant.parse(fila.getValue(COL_CREADO_EN) as String),
                )
            }
        }
        return resultado
    }
}
