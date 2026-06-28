package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.geopackage.features.user.FeatureRow
import mil.nga.sf.GeometryType
import java.time.Instant

/**
 * §5.4: detalle persistido de un conflicto que el sincronizador (M5) no
 * resolvió automáticamente. Guarda ambas versiones (la local que se intentó
 * subir y, si ArcGIS la devolvió, la del servidor) para que la pantalla de
 * "Conflictos pendientes" pueda mostrarlas y el coordinador decida.
 *
 * `colaSincronizacionId` enlaza con el ítem original de la cola para poder
 * reintentar/descartar una vez resuelto manualmente (la resolución en sí —
 * p. ej. "descartar cambio local" — queda fuera de alcance de M5; ver
 * limitaciones del README).
 */
data class ConflictoSincronizacion(
    val id: Long = 0,
    val colaSincronizacionId: Long,
    val tablaOrigen: TablaOrigen,
    val entidadId: Long,
    val tipo: TipoConflictoSincronizacion,
    val payloadLocalJson: String,
    val payloadServidorJson: String? = null,
    val mensaje: String,
    val creadoEn: Instant = Instant.now(),
)

private const val COL_COLA_SINCRONIZACION_ID = "cola_sincronizacion_id"
private const val COL_TABLA_ORIGEN = "tabla_origen"
private const val COL_ENTIDAD_ID = "entidad_id"
private const val COL_TIPO = "tipo"
private const val COL_PAYLOAD_LOCAL_JSON = "payload_local_json"
private const val COL_PAYLOAD_SERVIDOR_JSON = "payload_servidor_json"
private const val COL_MENSAJE = "mensaje"
private const val COL_CREADO_EN = "creado_en"

/** Igual que `cola_sincronizacion` (§4.9), sin geometría propia. */
class ConflictoSincronizacionRepository(private val context: Context) {

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_CONFLICTO_SINCRONIZACION,
            tipoGeometria = GeometryType.POINT,
            geometriaOpcional = true,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(COL_COLA_SINCRONIZACION_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_TABLA_ORIGEN, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ENTIDAD_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_TIPO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_PAYLOAD_LOCAL_JSON, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_PAYLOAD_SERVIDOR_JSON, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_MENSAJE, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_CREADO_EN, GeoPackageDataType.TEXT),
            ),
        )
    }

    fun insertar(conflicto: ConflictoSincronizacion): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_CONFLICTO_SINCRONIZACION)
        val fila = dao.newRow()
        fila.setValue(COL_COLA_SINCRONIZACION_ID, conflicto.colaSincronizacionId)
        fila.setValue(COL_TABLA_ORIGEN, conflicto.tablaOrigen.name)
        fila.setValue(COL_ENTIDAD_ID, conflicto.entidadId)
        fila.setValue(COL_TIPO, conflicto.tipo.name)
        fila.setValue(COL_PAYLOAD_LOCAL_JSON, conflicto.payloadLocalJson)
        fila.setValue(COL_PAYLOAD_SERVIDOR_JSON, conflicto.payloadServidorJson)
        fila.setValue(COL_MENSAJE, conflicto.mensaje)
        fila.setValue(COL_CREADO_EN, conflicto.creadoEn.toString())
        return dao.create(fila)
    }

    fun listarTodos(): List<ConflictoSincronizacion> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_CONFLICTO_SINCRONIZACION)
        val resultado = mutableListOf<ConflictoSincronizacion>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                resultado += filaAConflicto(cursor.row)
            }
        }
        return resultado
    }

    /** Descarta el conflicto de la lista (p. ej. una vez resuelto manualmente fuera de la app). */
    fun eliminar(id: Long): Boolean {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_CONFLICTO_SINCRONIZACION)
        return dao.deleteById(id) > 0
    }

    private fun filaAConflicto(fila: FeatureRow): ConflictoSincronizacion = ConflictoSincronizacion(
        id = fila.id,
        colaSincronizacionId = (fila.getValue(COL_COLA_SINCRONIZACION_ID) as Number).toLong(),
        tablaOrigen = TablaOrigen.valueOf(fila.getValue(COL_TABLA_ORIGEN) as String),
        entidadId = (fila.getValue(COL_ENTIDAD_ID) as Number).toLong(),
        tipo = TipoConflictoSincronizacion.valueOf(fila.getValue(COL_TIPO) as String),
        payloadLocalJson = fila.getValue(COL_PAYLOAD_LOCAL_JSON) as String,
        payloadServidorJson = fila.getValue(COL_PAYLOAD_SERVIDOR_JSON) as String?,
        mensaje = fila.getValue(COL_MENSAJE) as String,
        creadoEn = Instant.parse(fila.getValue(COL_CREADO_EN) as String),
    )
}
