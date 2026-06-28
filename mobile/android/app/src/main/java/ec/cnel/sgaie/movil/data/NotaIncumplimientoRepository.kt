package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.sf.GeometryType
import org.json.JSONObject
import java.time.Instant

/** Dominio §4.5: nota de incumplimiento sobre una entidad (equivalente de campo a `Novedad`, §6.13). */
data class NotaIncumplimiento(
    val id: Long = 0,
    val globalId: String,
    val entidadTipo: EntidadTipo,
    val entidadId: Long,
    val tipoIncumplimiento: TipoIncumplimiento,
    val descripcion: String,
    val gravedad: Gravedad,
    val fecha: Instant = Instant.now(),
    val estadoSubsanacion: EstadoSubsanacion = EstadoSubsanacion.PENDIENTE,
    val operacionPendiente: OperacionPendiente = OperacionPendiente.CREAR,
)

private const val COL_ENTIDAD_TIPO = "entidad_tipo"
private const val COL_ENTIDAD_ID = "entidad_id"
private const val COL_TIPO_INCUMPLIMIENTO = "tipo_incumplimiento"
private const val COL_DESCRIPCION = "descripcion"
private const val COL_GRAVEDAD = "gravedad"
private const val COL_FECHA = "fecha"
private const val COL_ESTADO_SUBSANACION = "estado_subsanacion"

/** Igual que `cola_sincronizacion` (§4.9), sin geometría propia: usa el patrón de geometría opcional nunca poblada. */
class NotaIncumplimientoRepository(private val context: Context) {

    private val colaSincronizacion = ColaSincronizacionRepository(context)

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_NOTA_INCUMPLIMIENTO,
            tipoGeometria = GeometryType.POINT,
            geometriaOpcional = true,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(GeoPackageContract.COL_GLOBAL_ID, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ENTIDAD_TIPO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ENTIDAD_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_TIPO_INCUMPLIMIENTO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_DESCRIPCION, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_GRAVEDAD, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_FECHA, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ESTADO_SUBSANACION, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(GeoPackageContract.COL_OPERACION_PENDIENTE, GeoPackageDataType.TEXT),
            ),
        )
    }

    /** Inserta la nota y la encola en `cola_sincronizacion` (§5.2: toda alta local se encola). */
    fun insertar(nota: NotaIncumplimiento): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_NOTA_INCUMPLIMIENTO)
        val fila = dao.newRow()
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, nota.globalId)
        fila.setValue(COL_ENTIDAD_TIPO, nota.entidadTipo.name)
        fila.setValue(COL_ENTIDAD_ID, nota.entidadId)
        fila.setValue(COL_TIPO_INCUMPLIMIENTO, nota.tipoIncumplimiento.name)
        fila.setValue(COL_DESCRIPCION, nota.descripcion)
        fila.setValue(COL_GRAVEDAD, nota.gravedad.name)
        fila.setValue(COL_FECHA, nota.fecha.toString())
        fila.setValue(COL_ESTADO_SUBSANACION, nota.estadoSubsanacion.name)
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, OperacionPendiente.CREAR.name)
        val idLocal = dao.create(fila)

        colaSincronizacion.encolar(
            tablaOrigen = TablaOrigen.NOTA_INCUMPLIMIENTO,
            entidadTipo = nota.entidadTipo,
            entidadId = idLocal,
            operacion = OperacionSincronizacion.CREAR,
            payloadJson = payloadJson(nota.copy(id = idLocal)),
        )
        return idLocal
    }

    fun listarPorEntidad(entidadTipo: EntidadTipo, entidadId: Long): List<NotaIncumplimiento> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_NOTA_INCUMPLIMIENTO)
        val resultado = mutableListOf<NotaIncumplimiento>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                if (EntidadTipo.valueOf(fila.getValue(COL_ENTIDAD_TIPO) as String) != entidadTipo) continue
                if ((fila.getValue(COL_ENTIDAD_ID) as Number).toLong() != entidadId) continue
                resultado += NotaIncumplimiento(
                    id = fila.id,
                    globalId = fila.getValue(GeoPackageContract.COL_GLOBAL_ID) as String,
                    entidadTipo = entidadTipo,
                    entidadId = entidadId,
                    tipoIncumplimiento = TipoIncumplimiento.valueOf(fila.getValue(COL_TIPO_INCUMPLIMIENTO) as String),
                    descripcion = fila.getValue(COL_DESCRIPCION) as String,
                    gravedad = Gravedad.valueOf(fila.getValue(COL_GRAVEDAD) as String),
                    fecha = Instant.parse(fila.getValue(COL_FECHA) as String),
                    estadoSubsanacion = EstadoSubsanacion.valueOf(fila.getValue(COL_ESTADO_SUBSANACION) as String),
                    operacionPendiente = OperacionPendiente.valueOf(
                        fila.getValue(GeoPackageContract.COL_OPERACION_PENDIENTE) as String,
                    ),
                )
            }
        }
        return resultado
    }

    private fun payloadJson(nota: NotaIncumplimiento): String = JSONObject().apply {
        put("id", nota.id)
        put("global_id", nota.globalId)
        put("entidad_tipo", nota.entidadTipo.name)
        put("entidad_id", nota.entidadId)
        put("tipo_incumplimiento", nota.tipoIncumplimiento.name)
        put("descripcion", nota.descripcion)
        put("gravedad", nota.gravedad.name)
        put("fecha", nota.fecha.toString())
        put("estado_subsanacion", nota.estadoSubsanacion.name)
    }.toString()
}
