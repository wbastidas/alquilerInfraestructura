package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.sf.GeometryType
import mil.nga.sf.Polygon
import java.time.Instant

/** Dominio §4.1: área/lote de trabajo descargado de ArcGIS. */
data class SectorTrabajo(
    val id: Long = 0,
    val globalId: String,
    val codigo: String,
    val nombre: String,
    val geometria: Polygon,
    val contratoIdReferencia: Int? = null,
    val unidadNegocioId: Int,
    val fechaExtraccion: Instant = Instant.now(),
    val fechaUltimaSync: Instant? = null,
    val estado: EstadoSectorTrabajo = EstadoSectorTrabajo.DESCARGADO,
    val usuarioResponsable: String,
    val operacionPendiente: OperacionPendiente = OperacionPendiente.NINGUNA,
)

private const val COL_CODIGO = "codigo"
private const val COL_NOMBRE = "nombre"
private const val COL_CONTRATO_ID_REFERENCIA = "contrato_id_referencia"
private const val COL_UNIDAD_NEGOCIO_ID = "unidad_negocio_id"
private const val COL_FECHA_EXTRACCION = "fecha_extraccion"
private const val COL_FECHA_ULTIMA_SYNC = "fecha_ultima_sync"
private const val COL_ESTADO = "estado"
private const val COL_USUARIO_RESPONSABLE = "usuario_responsable"

class SectorTrabajoRepository(private val context: Context) {

    fun crearTablaSiNoExiste() {
        val geoPackage = GeoPackageProvider.obtener(context)
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = geoPackage,
            nombreTabla = GeoPackageContract.TABLA_SECTOR_TRABAJO,
            tipoGeometria = GeometryType.POLYGON,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(GeoPackageContract.COL_GLOBAL_ID, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_CODIGO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_NOMBRE, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_CONTRATO_ID_REFERENCIA, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_UNIDAD_NEGOCIO_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_FECHA_EXTRACCION, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_FECHA_ULTIMA_SYNC, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ESTADO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_USUARIO_RESPONSABLE, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(GeoPackageContract.COL_OPERACION_PENDIENTE, GeoPackageDataType.TEXT),
            ),
        )
    }

    fun insertar(sector: SectorTrabajo): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_SECTOR_TRABAJO)
        val fila = dao.newRow()
        fila.geometry = mil.nga.geopackage.geom.GeoPackageGeometryData(sector.geometria)
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, sector.globalId)
        fila.setValue(COL_CODIGO, sector.codigo)
        fila.setValue(COL_NOMBRE, sector.nombre)
        fila.setValue(COL_CONTRATO_ID_REFERENCIA, sector.contratoIdReferencia)
        fila.setValue(COL_UNIDAD_NEGOCIO_ID, sector.unidadNegocioId)
        fila.setValue(COL_FECHA_EXTRACCION, sector.fechaExtraccion.toString())
        fila.setValue(COL_FECHA_ULTIMA_SYNC, sector.fechaUltimaSync?.toString())
        fila.setValue(COL_ESTADO, sector.estado.name)
        fila.setValue(COL_USUARIO_RESPONSABLE, sector.usuarioResponsable)
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, sector.operacionPendiente.name)
        return dao.create(fila)
    }

    /**
     * §5.3/§5.4: marca el resultado de un ciclo de sincronización sobre el
     * sector (`SINCRONIZADO` si todo se aplicó, `CON_CONFLICTOS` si quedó
     * algún ítem en `CONFLICTO`) y estampa `fecha_ultima_sync`.
     */
    fun actualizarEstado(id: Long, estado: EstadoSectorTrabajo, fechaUltimaSync: Instant = Instant.now()): Boolean {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_SECTOR_TRABAJO)
        val fila = dao.queryForIdRow(id) ?: return false
        fila.setValue(COL_ESTADO, estado.name)
        fila.setValue(COL_FECHA_ULTIMA_SYNC, fechaUltimaSync.toString())
        dao.update(fila)
        return true
    }

    fun listarTodos(): List<SectorTrabajo> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_SECTOR_TRABAJO)
        val resultado = mutableListOf<SectorTrabajo>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                resultado += SectorTrabajo(
                    id = fila.id,
                    globalId = fila.getValue(GeoPackageContract.COL_GLOBAL_ID) as String,
                    codigo = fila.getValue(COL_CODIGO) as String,
                    nombre = fila.getValue(COL_NOMBRE) as String,
                    geometria = fila.geometry.geometry as Polygon,
                    contratoIdReferencia = (fila.getValue(COL_CONTRATO_ID_REFERENCIA) as Number?)?.toInt(),
                    unidadNegocioId = (fila.getValue(COL_UNIDAD_NEGOCIO_ID) as Number).toInt(),
                    fechaExtraccion = Instant.parse(fila.getValue(COL_FECHA_EXTRACCION) as String),
                    fechaUltimaSync = (fila.getValue(COL_FECHA_ULTIMA_SYNC) as String?)?.let(Instant::parse),
                    estado = EstadoSectorTrabajo.valueOf(fila.getValue(COL_ESTADO) as String),
                    usuarioResponsable = fila.getValue(COL_USUARIO_RESPONSABLE) as String,
                    operacionPendiente = OperacionPendiente.valueOf(
                        fila.getValue(GeoPackageContract.COL_OPERACION_PENDIENTE) as String,
                    ),
                )
            }
        }
        return resultado
    }
}
