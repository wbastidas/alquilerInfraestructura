package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.geopackage.geom.GeoPackageGeometryData
import mil.nga.sf.GeometryType
import mil.nga.sf.LineString

/** Dominio §4.3: tramo de red entre dos postes (o trazado libre). */
data class TramoRed(
    val id: Long = 0,
    val globalId: String,
    val sectorTrabajoId: Long,
    val posteOrigenId: Long? = null,
    val posteDestinoId: Long? = null,
    val geometria: LineString,
    val tipoRed: TipoRed,
    val longitudM: Double? = null,
    val estado: EstadoTramoRed = EstadoTramoRed.ACTIVA,
    val operacionPendiente: OperacionPendiente = OperacionPendiente.NINGUNA,
)

private const val COL_SECTOR_TRABAJO_ID = "sector_trabajo_id"
private const val COL_POSTE_ORIGEN_ID = "poste_origen_id"
private const val COL_POSTE_DESTINO_ID = "poste_destino_id"
private const val COL_TIPO_RED = "tipo_red"
private const val COL_LONGITUD_M = "longitud_m"
private const val COL_ESTADO = "estado"

class TramoRedRepository(private val context: Context) {

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_TRAMO_RED,
            tipoGeometria = GeometryType.LINESTRING,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(GeoPackageContract.COL_GLOBAL_ID, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_SECTOR_TRABAJO_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_POSTE_ORIGEN_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_POSTE_DESTINO_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_TIPO_RED, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_LONGITUD_M, GeoPackageDataType.DOUBLE),
                FeatureColumn.createColumn(COL_ESTADO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(GeoPackageContract.COL_OPERACION_PENDIENTE, GeoPackageDataType.TEXT),
            ),
        )
    }

    fun insertar(tramo: TramoRed): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_TRAMO_RED)
        val fila = dao.newRow()
        fila.geometry = GeoPackageGeometryData(tramo.geometria)
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, tramo.globalId)
        fila.setValue(COL_SECTOR_TRABAJO_ID, tramo.sectorTrabajoId)
        fila.setValue(COL_POSTE_ORIGEN_ID, tramo.posteOrigenId)
        fila.setValue(COL_POSTE_DESTINO_ID, tramo.posteDestinoId)
        fila.setValue(COL_TIPO_RED, tramo.tipoRed.name)
        fila.setValue(COL_LONGITUD_M, tramo.longitudM)
        fila.setValue(COL_ESTADO, tramo.estado.name)
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, tramo.operacionPendiente.name)
        return dao.create(fila)
    }

    fun listarPorSector(sectorTrabajoId: Long): List<TramoRed> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_TRAMO_RED)
        val resultado = mutableListOf<TramoRed>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                if ((fila.getValue(COL_SECTOR_TRABAJO_ID) as Number).toLong() != sectorTrabajoId) continue
                resultado += TramoRed(
                    id = fila.id,
                    globalId = fila.getValue(GeoPackageContract.COL_GLOBAL_ID) as String,
                    sectorTrabajoId = sectorTrabajoId,
                    posteOrigenId = (fila.getValue(COL_POSTE_ORIGEN_ID) as Number?)?.toLong(),
                    posteDestinoId = (fila.getValue(COL_POSTE_DESTINO_ID) as Number?)?.toLong(),
                    geometria = fila.geometry.geometry as LineString,
                    tipoRed = TipoRed.valueOf(fila.getValue(COL_TIPO_RED) as String),
                    longitudM = fila.getValue(COL_LONGITUD_M) as Double?,
                    estado = EstadoTramoRed.valueOf(fila.getValue(COL_ESTADO) as String),
                    operacionPendiente = OperacionPendiente.valueOf(
                        fila.getValue(GeoPackageContract.COL_OPERACION_PENDIENTE) as String,
                    ),
                )
            }
        }
        return resultado
    }
}
