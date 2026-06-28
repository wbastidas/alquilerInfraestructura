package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.db.GeoPackageDataType
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.geopackage.geom.GeoPackageGeometryData
import mil.nga.sf.GeometryType
import mil.nga.sf.Point
import java.time.LocalDate

/**
 * Dominio §4.4. La especificación no fija una columna de geometría propia
 * (el equipo normalmente hereda la ubicación de `poste_id`), pero sí permite
 * `poste_id` nulo ("equipo no está montado en poste registrado"); para que
 * ese caso sea igualmente visualizable en el mapa (§6: "capas superpuestas
 * ... equipos ... se dibujan directamente desde el GeoPackage local") se
 * agrega aquí una columna de geometría opcional (nullable).
 */
data class EquipoTelecomunicacion(
    val id: Long = 0,
    val globalId: String,
    val posteId: Long? = null,
    val geometria: Point? = null,
    val tipoEquipo: TipoEquipo,
    val marca: String? = null,
    val modelo: String? = null,
    val numeroSerie: String? = null,
    val fechaInstalacion: LocalDate? = null,
    val estado: EstadoEquipo = EstadoEquipo.OPERATIVO,
    val operacionPendiente: OperacionPendiente = OperacionPendiente.NINGUNA,
)

private const val COL_POSTE_ID = "poste_id"
private const val COL_TIPO_EQUIPO = "tipo_equipo"
private const val COL_MARCA = "marca"
private const val COL_MODELO = "modelo"
private const val COL_NUMERO_SERIE = "numero_serie"
private const val COL_FECHA_INSTALACION = "fecha_instalacion"
private const val COL_ESTADO = "estado"

class EquipoTelecomunicacionRepository(private val context: Context) {

    fun crearTablaSiNoExiste() {
        GeoPackageProvider.crearTablaSiNoExiste(
            geoPackage = GeoPackageProvider.obtener(context),
            nombreTabla = GeoPackageContract.TABLA_EQUIPO_TELECOMUNICACION,
            tipoGeometria = GeometryType.POINT,
            geometriaOpcional = true,
            columnasAdicionales = listOf(
                FeatureColumn.createColumn(GeoPackageContract.COL_GLOBAL_ID, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_POSTE_ID, GeoPackageDataType.MEDIUMINT),
                FeatureColumn.createColumn(COL_TIPO_EQUIPO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_MARCA, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_MODELO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_NUMERO_SERIE, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_FECHA_INSTALACION, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(COL_ESTADO, GeoPackageDataType.TEXT),
                FeatureColumn.createColumn(GeoPackageContract.COL_OPERACION_PENDIENTE, GeoPackageDataType.TEXT),
            ),
        )
    }

    fun insertar(equipo: EquipoTelecomunicacion): Long {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context)
            .getFeatureDao(GeoPackageContract.TABLA_EQUIPO_TELECOMUNICACION)
        val fila = dao.newRow()
        fila.geometry = equipo.geometria?.let { GeoPackageGeometryData(it) }
        fila.setValue(GeoPackageContract.COL_GLOBAL_ID, equipo.globalId)
        fila.setValue(COL_POSTE_ID, equipo.posteId)
        fila.setValue(COL_TIPO_EQUIPO, equipo.tipoEquipo.name)
        fila.setValue(COL_MARCA, equipo.marca)
        fila.setValue(COL_MODELO, equipo.modelo)
        fila.setValue(COL_NUMERO_SERIE, equipo.numeroSerie)
        fila.setValue(COL_FECHA_INSTALACION, equipo.fechaInstalacion?.toString())
        fila.setValue(COL_ESTADO, equipo.estado.name)
        fila.setValue(GeoPackageContract.COL_OPERACION_PENDIENTE, equipo.operacionPendiente.name)
        return dao.create(fila)
    }

    fun listarPorPoste(posteId: Long): List<EquipoTelecomunicacion> {
        crearTablaSiNoExiste()
        val dao = GeoPackageProvider.obtener(context)
            .getFeatureDao(GeoPackageContract.TABLA_EQUIPO_TELECOMUNICACION)
        val resultado = mutableListOf<EquipoTelecomunicacion>()
        dao.queryForAll().use { cursor ->
            while (cursor.moveToNext()) {
                val fila = cursor.row
                if ((fila.getValue(COL_POSTE_ID) as Number?)?.toLong() != posteId) continue
                resultado += EquipoTelecomunicacion(
                    id = fila.id,
                    globalId = fila.getValue(GeoPackageContract.COL_GLOBAL_ID) as String,
                    posteId = posteId,
                    geometria = fila.geometry?.geometry as Point?,
                    tipoEquipo = TipoEquipo.valueOf(fila.getValue(COL_TIPO_EQUIPO) as String),
                    marca = fila.getValue(COL_MARCA) as String?,
                    modelo = fila.getValue(COL_MODELO) as String?,
                    numeroSerie = fila.getValue(COL_NUMERO_SERIE) as String?,
                    fechaInstalacion = (fila.getValue(COL_FECHA_INSTALACION) as String?)?.let(LocalDate::parse),
                    estado = EstadoEquipo.valueOf(fila.getValue(COL_ESTADO) as String),
                    operacionPendiente = OperacionPendiente.valueOf(
                        fila.getValue(GeoPackageContract.COL_OPERACION_PENDIENTE) as String,
                    ),
                )
            }
        }
        return resultado
    }
}
