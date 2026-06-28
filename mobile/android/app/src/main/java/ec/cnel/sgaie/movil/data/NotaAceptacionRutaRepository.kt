package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.geopackage.geom.GeoPackageGeometryData
import mil.nga.sf.GeometryType
import mil.nga.sf.LineString
import org.json.JSONObject
import java.time.Instant

/** Dominio §4.6: verificación en campo de una ruta (equivalente a `InformeFactibilidad.rutas_verificadas`, §6.9). */
data class NotaAceptacionRuta(
    val id: Long = 0,
    val globalId: String,
    val sectorTrabajoId: Long,
    val rutaReferencia: String? = null,
    val geometria: LineString? = null,
    val decision: DecisionAceptacionRuta,
    val comentario: String,
    val fecha: Instant = Instant.now(),
    val operacionPendiente: OperacionPendiente = OperacionPendiente.CREAR,
)

private const val COL_SECTOR_TRABAJO_ID = "sector_trabajo_id"
private const val COL_RUTA_REFERENCIA = "ruta_referencia"
private const val COL_DECISION = "decision"
private const val COL_COMENTARIO = "comentario"
private const val COL_FECHA = "fecha"

class NotaAceptacionRutaRepository(private val context: Context) {

    private val colaSincronizacion = ColaSincronizacionRepository(context)

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_NOTA_ACEPTACION_RUTA,
            tipoGeometria = GeometryType.LINESTRING,
            geometriaOpcional = true,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(GeoPackageContract.COL_GLOBAL_ID, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_SECTOR_TRABAJO_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_RUTA_REFERENCIA, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_DECISION, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_COMENTARIO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_FECHA, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(GeoPackageContract.COL_OPERACION_PENDIENTE, GeoPackageDataType.TEXT),
            ),
        )
    }

    /** Inserta la nota y la encola en `cola_sincronizacion` (§5.2: toda alta local se encola). */
    fun insertar(nota: NotaAceptacionRuta): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_NOTA_ACEPTACION_RUTA)
        val fila = dao.newRow()
        fila.geometry = nota.geometria?.let { GeoPackageGeometryData(it) }
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, nota.globalId)
        fila.setValue(COL_SECTOR_TRABAJO_ID, nota.sectorTrabajoId)
        fila.setValue(COL_RUTA_REFERENCIA, nota.rutaReferencia)
        fila.setValue(COL_DECISION, nota.decision.name)
        fila.setValue(COL_COMENTARIO, nota.comentario)
        fila.setValue(COL_FECHA, nota.fecha.toString())
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, OperacionPendiente.CREAR.name)
        val idLocal = dao.create(fila)

        colaSincronizacion.encolar(
            tablaOrigen = TablaOrigen.NOTA_ACEPTACION_RUTA,
            entidadTipo = EntidadTipo.SECTOR,
            entidadId = idLocal,
            operacion = OperacionSincronizacion.CREAR,
            payloadJson = payloadJson(nota.copy(id = idLocal)),
        )
        return idLocal
    }

    fun listarPorSector(sectorTrabajoId: Long): List<NotaAceptacionRuta> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_NOTA_ACEPTACION_RUTA)
        val resultado = mutableListOf<NotaAceptacionRuta>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                if ((fila.getValue(COL_SECTOR_TRABAJO_ID) as Number).toLong() != sectorTrabajoId) continue
                resultado += NotaAceptacionRuta(
                    id = fila.id,
                    globalId = fila.getValue(GeoPackageContract.COL_GLOBAL_ID) as String,
                    sectorTrabajoId = sectorTrabajoId,
                    rutaReferencia = fila.getValue(COL_RUTA_REFERENCIA) as String?,
                    geometria = fila.geometry?.geometry as LineString?,
                    decision = DecisionAceptacionRuta.valueOf(fila.getValue(COL_DECISION) as String),
                    comentario = fila.getValue(COL_COMENTARIO) as String,
                    fecha = Instant.parse(fila.getValue(COL_FECHA) as String),
                    operacionPendiente = OperacionPendiente.valueOf(
                        fila.getValue(GeoPackageContract.COL_OPERACION_PENDIENTE) as String,
                    ),
                )
            }
        }
        return resultado
    }

    private fun payloadJson(nota: NotaAceptacionRuta): String = JSONObject().apply {
        put("id", nota.id)
        put("global_id", nota.globalId)
        put("sector_trabajo_id", nota.sectorTrabajoId)
        put("ruta_referencia", nota.rutaReferencia)
        put("decision", nota.decision.name)
        put("comentario", nota.comentario)
        put("fecha", nota.fecha.toString())
    }.toString()
}
