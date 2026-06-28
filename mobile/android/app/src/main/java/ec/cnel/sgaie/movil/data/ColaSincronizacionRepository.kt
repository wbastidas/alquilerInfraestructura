package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.sf.GeometryType
import java.time.Instant

/**
 * Dominio §4.9: cola de cambios pendientes de subir a ArcGIS (outbox, §5.2).
 * Toda alta/edición/eliminación local de poste/tramo_red/equipo/nota/foto
 * encola aquí un snapshot JSON del registro, que M5 lee para `applyEdits`.
 */
data class ItemColaSincronizacion(
    val id: Long = 0,
    val tablaOrigen: TablaOrigen,
    val entidadTipo: EntidadTipo,
    val entidadId: Long,
    val operacion: OperacionSincronizacion,
    val payloadJson: String,
    val intentos: Int = 0,
    val estado: EstadoSincronizacion = EstadoSincronizacion.PENDIENTE,
    val mensajeError: String? = null,
    val creadoEn: Instant = Instant.now(),
)

private const val COL_TABLA_ORIGEN = "tabla_origen"
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
                FeatureColumn.createColumn(COL_TABLA_ORIGEN, GeoPackageDataType.TEXT),
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

    fun encolar(
        tablaOrigen: TablaOrigen,
        entidadTipo: EntidadTipo,
        entidadId: Long,
        operacion: OperacionSincronizacion,
        payloadJson: String,
    ): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_COLA_SINCRONIZACION)
        val fila = dao.newRow()
        fila.setValue(COL_TABLA_ORIGEN, tablaOrigen.name)
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
                resultado += filaAItem(fila.id, fila)
            }
        }
        return resultado
    }

    /** Igual que [listarPendientes] pero sin filtrar por estado, para recomputar el estado de un sector tras un ciclo de sincronización (§5.3/§5.4). */
    fun listarTodos(): List<ItemColaSincronizacion> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_COLA_SINCRONIZACION)
        val resultado = mutableListOf<ItemColaSincronizacion>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                resultado += filaAItem(fila.id, fila)
            }
        }
        return resultado
    }

    /** Marca el ítem como `ENVIADO` (cambio aceptado por ArcGIS) tras un ciclo de sincronización exitoso (§5.3). */
    fun marcarEnviado(id: Long) = actualizarEstado(id, EstadoSincronizacion.ENVIADO, mensajeError = null)

    /** Marca el ítem como `ERROR` reintentable (rechazo de ArcGIS que no es el caso de conflicto de §5.4). */
    fun marcarError(id: Long, mensaje: String) = actualizarEstado(id, EstadoSincronizacion.ERROR, mensajeError = mensaje)

    /** Marca el ítem como `CONFLICTO`: queda visible en la pantalla de "Conflictos pendientes" (§5.4), nunca se reintenta solo. */
    fun marcarConflicto(id: Long, mensaje: String) = actualizarEstado(id, EstadoSincronizacion.CONFLICTO, mensajeError = mensaje)

    /**
     * `# NOTA: queryForIdRow/update sobre FeatureDao no se pudo verificar contra
     * la versión real de geopackage-android resuelta (§13/limitaciones de este
     * entorno), igual que el resto de la API de bajo nivel usada en este scaffold.`
     */
    private fun actualizarEstado(id: Long, estado: EstadoSincronizacion, mensajeError: String?): Boolean {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context).getFeatureDao(GeoPackageContract.TABLA_COLA_SINCRONIZACION)
        val fila = dao.queryForIdRow(id) ?: return false
        val intentosActuales = (fila.getValue(COL_INTENTOS) as Number?)?.toInt() ?: 0
        fila.setValue(COL_ESTADO, estado.name)
        fila.setValue(COL_MENSAJE_ERROR, mensajeError)
        fila.setValue(COL_INTENTOS, intentosActuales + 1)
        dao.update(fila)
        return true
    }

    private fun filaAItem(id: Long, fila: mil.nga.geopackage.features.user.FeatureRow): ItemColaSincronizacion = ItemColaSincronizacion(
        id = id,
        tablaOrigen = TablaOrigen.valueOf(fila.getValue(COL_TABLA_ORIGEN) as String),
        entidadTipo = EntidadTipo.valueOf(fila.getValue(COL_ENTIDAD_TIPO) as String),
        entidadId = (fila.getValue(COL_ENTIDAD_ID) as Number).toLong(),
        operacion = OperacionSincronizacion.valueOf(fila.getValue(COL_OPERACION) as String),
        payloadJson = fila.getValue(COL_PAYLOAD_JSON) as String,
        intentos = (fila.getValue(COL_INTENTOS) as Number).toInt(),
        estado = EstadoSincronizacion.valueOf(fila.getValue(COL_ESTADO) as String),
        mensajeError = fila.getValue(COL_MENSAJE_ERROR) as String?,
        creadoEn = Instant.parse(fila.getValue(COL_CREADO_EN) as String),
    )
}
