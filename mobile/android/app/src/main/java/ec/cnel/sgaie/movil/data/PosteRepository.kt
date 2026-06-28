package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.geopackage.features.user.FeatureRow
import mil.nga.geopackage.geom.GeoPackageGeometryData
import mil.nga.sf.GeometryType
import mil.nga.sf.Point
import org.json.JSONObject
import java.time.Instant

/** Dominio §4.2: poste de la red, dentro de un sector_trabajo. */
data class Poste(
    val id: Long = 0,
    val globalId: String,
    val sectorTrabajoId: Long,
    val codigoPoste: String,
    val geometria: Point,
    val tipoPoste: TipoPoste,
    val alturaM: Double? = null,
    val capacidadCables: Int? = null,
    val estadoFisico: EstadoFisicoPoste = EstadoFisicoPoste.BUENO,
    val fechaInspeccion: Instant? = null,
    val observaciones: String? = null,
    val operacionPendiente: OperacionPendiente = OperacionPendiente.NINGUNA,
)

private const val COL_SECTOR_TRABAJO_ID = "sector_trabajo_id"
private const val COL_CODIGO_POSTE = "codigo_poste"
private const val COL_TIPO_POSTE = "tipo_poste"
private const val COL_ALTURA_M = "altura_m"
private const val COL_CAPACIDAD_CABLES = "capacidad_cables"
private const val COL_ESTADO_FISICO = "estado_fisico"
private const val COL_FECHA_INSPECCION = "fecha_inspeccion"
private const val COL_OBSERVACIONES = "observaciones"

class PosteRepository(private val context: Context) {

    private val colaSincronizacion = ColaSincronizacionRepository(context)

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_POSTE,
            tipoGeometria = GeometryType.POINT,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(GeoPackageContract.COL_GLOBAL_ID, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_SECTOR_TRABAJO_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_CODIGO_POSTE, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_TIPO_POSTE, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ALTURA_M, GeoPackageDataType.DOUBLE),
                FeatureColumn.createColumn(COL_CAPACIDAD_CABLES, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_ESTADO_FISICO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_FECHA_INSPECCION, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_OBSERVACIONES, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(GeoPackageContract.COL_OPERACION_PENDIENTE, GeoPackageDataType.TEXT),
            ),
        )
    }

    fun insertar(poste: Poste): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_POSTE)
        val fila = dao.newRow()
        fila.geometry = GeoPackageGeometryData(poste.geometria)
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, poste.globalId)
        fila.setValue(COL_SECTOR_TRABAJO_ID, poste.sectorTrabajoId)
        fila.setValue(COL_CODIGO_POSTE, poste.codigoPoste)
        fila.setValue(COL_TIPO_POSTE, poste.tipoPoste.name)
        fila.setValue(COL_ALTURA_M, poste.alturaM)
        fila.setValue(COL_CAPACIDAD_CABLES, poste.capacidadCables)
        fila.setValue(COL_ESTADO_FISICO, poste.estadoFisico.name)
        fila.setValue(COL_FECHA_INSPECCION, poste.fechaInspeccion?.toString())
        fila.setValue(COL_OBSERVACIONES, poste.observaciones)
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, poste.operacionPendiente.name)
        return dao.create(fila)
    }

    /**
     * Actualiza el poste y encola un `EDITAR` en `cola_sincronizacion` (§5.2).
     *
     * `# NOTA: queryForIdRow/update sobre FeatureDao no se pudo verificar contra
     * la versión real de geopackage-android resuelta (§13/limitaciones de este
     * entorno), igual que el resto de la API de bajo nivel usada en este scaffold.`
     */
    fun actualizar(poste: Poste): Boolean {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_POSTE)
        val fila = dao.queryForIdRow(poste.id) ?: return false
        fila.geometry = GeoPackageGeometryData(poste.geometria)
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, poste.globalId)
        fila.setValue(COL_SECTOR_TRABAJO_ID, poste.sectorTrabajoId)
        fila.setValue(COL_CODIGO_POSTE, poste.codigoPoste)
        fila.setValue(COL_TIPO_POSTE, poste.tipoPoste.name)
        fila.setValue(COL_ALTURA_M, poste.alturaM)
        fila.setValue(COL_CAPACIDAD_CABLES, poste.capacidadCables)
        fila.setValue(COL_ESTADO_FISICO, poste.estadoFisico.name)
        fila.setValue(COL_FECHA_INSPECCION, poste.fechaInspeccion?.toString())
        fila.setValue(COL_OBSERVACIONES, poste.observaciones)
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, OperacionPendiente.EDITAR.name)
        dao.update(fila)

        val posteActualizado = poste.copy(operacionPendiente = OperacionPendiente.EDITAR)
        colaSincronizacion.encolar(
            tablaOrigen = TablaOrigen.POSTE,
            entidadTipo = EntidadTipo.POSTE,
            entidadId = poste.id,
            operacion = OperacionSincronizacion.EDITAR,
            payloadJson = payloadJson(posteActualizado),
        )
        return true
    }

    /** Elimina el poste y encola un `ELIMINAR` en `cola_sincronizacion` con el último snapshot conocido (§5.2). */
    fun eliminar(id: Long): Boolean {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_POSTE)
        val fila = dao.queryForIdRow(id) ?: return false
        val poste = filaAPoste(fila)
        dao.deleteById(id)

        colaSincronizacion.encolar(
            tablaOrigen = TablaOrigen.POSTE,
            entidadTipo = EntidadTipo.POSTE,
            entidadId = id,
            operacion = OperacionSincronizacion.ELIMINAR,
            payloadJson = payloadJson(poste.copy(operacionPendiente = OperacionPendiente.ELIMINAR)),
        )
        return true
    }

    fun obtenerPorId(id: Long): Poste? {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_POSTE)
        val fila = dao.queryForIdRow(id) ?: return null
        return filaAPoste(fila)
    }

    fun listarPorSector(sectorTrabajoId: Long): List<Poste> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_POSTE)
        val resultado = mutableListOf<Poste>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                if ((fila.getValue(COL_SECTOR_TRABAJO_ID) as Number).toLong() != sectorTrabajoId) continue
                resultado += filaAPoste(fila)
            }
        }
        return resultado
    }

    private fun filaAPoste(fila: FeatureRow): Poste = Poste(
        id = fila.id,
        globalId = fila.getValue(GeoPackageContract.COL_GLOBAL_ID) as String,
        sectorTrabajoId = (fila.getValue(COL_SECTOR_TRABAJO_ID) as Number).toLong(),
        codigoPoste = fila.getValue(COL_CODIGO_POSTE) as String,
        geometria = fila.geometry.geometry as Point,
        tipoPoste = TipoPoste.valueOf(fila.getValue(COL_TIPO_POSTE) as String),
        alturaM = fila.getValue(COL_ALTURA_M) as Double?,
        capacidadCables = (fila.getValue(COL_CAPACIDAD_CABLES) as Number?)?.toInt(),
        estadoFisico = EstadoFisicoPoste.valueOf(fila.getValue(COL_ESTADO_FISICO) as String),
        fechaInspeccion = (fila.getValue(COL_FECHA_INSPECCION) as String?)?.let(Instant::parse),
        observaciones = fila.getValue(COL_OBSERVACIONES) as String?,
        operacionPendiente = OperacionPendiente.valueOf(
            fila.getValue(GeoPackageContract.COL_OPERACION_PENDIENTE) as String,
        ),
    )

    private fun payloadJson(poste: Poste): String = JSONObject().apply {
        put("id", poste.id)
        put("global_id", poste.globalId)
        put("sector_trabajo_id", poste.sectorTrabajoId)
        put("codigo_poste", poste.codigoPoste)
        put("tipo_poste", poste.tipoPoste.name)
        put("altura_m", poste.alturaM)
        put("capacidad_cables", poste.capacidadCables)
        put("estado_fisico", poste.estadoFisico.name)
        put("fecha_inspeccion", poste.fechaInspeccion?.toString())
        put("observaciones", poste.observaciones)
    }.toString()
}
