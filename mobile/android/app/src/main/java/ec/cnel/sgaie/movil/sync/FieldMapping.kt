package ec.cnel.sgaie.movil.sync

import ec.cnel.sgaie.movil.data.EquipoTelecomunicacion
import ec.cnel.sgaie.movil.data.EstadoEquipo
import ec.cnel.sgaie.movil.data.EstadoFisicoPoste
import ec.cnel.sgaie.movil.data.EstadoTramoRed
import ec.cnel.sgaie.movil.data.OperacionPendiente
import ec.cnel.sgaie.movil.data.Poste
import ec.cnel.sgaie.movil.data.TipoEquipo
import ec.cnel.sgaie.movil.data.TipoPoste
import ec.cnel.sgaie.movil.data.TipoRed
import ec.cnel.sgaie.movil.data.TramoRed
import mil.nga.sf.LineString
import mil.nga.sf.Point
import mil.nga.sf.wkb.GeometryReader
import java.time.LocalDate
import java.util.UUID

/**
 * Traduce filas crudas leídas por [ReplicaGeodatabaseReader] (provenientes
 * de las capas de ArcGIS) a las entidades GeoPackage locales (§4).
 *
 * El mobile geodatabase de ArcGIS (`dataFormat=sqlite` en `createReplica`)
 * está basado en el estándar OGC GeoPackage desde ArcGIS Pro/Runtime
 * recientes, por lo que la columna de geometría (`Shape` por convención de
 * Esri) se asume codificada en WKB estándar, decodificable con la misma
 * librería NGA Simple Features que ya usa el GeoPackage local.
 *
 * `# TODO: confirmar contra el servicio real de CNEL EP los nombres exactos
 * de columnas de cada capa (los usados abajo son los nombres en español del
 * propio modelo de datos GeoPackage de este documento, bajo el supuesto de
 * que el Feature Service de origen ya los expone así; si ArcGIS expone
 * nombres distintos, ajustar las constantes COL_* de cada bloque) — ver §13.`
 */
object FieldMapping {

    private const val COL_SHAPE = "Shape"
    private const val COL_GLOBAL_ID = "GlobalID"

    fun filaAPoste(fila: Map<String, Any?>, sectorTrabajoId: Long): Poste {
        return Poste(
            globalId = fila.textoOGenerar(COL_GLOBAL_ID),
            sectorTrabajoId = sectorTrabajoId,
            codigoPoste = fila.texto("codigo_poste"),
            geometria = fila.geometriaPunto(),
            tipoPoste = fila.enumeracion("tipo_poste", TipoPoste.OTRO) { TipoPoste.valueOf(it) },
            alturaM = fila.decimalONulo("altura_m"),
            capacidadCables = fila.enteroONulo("capacidad_cables"),
            estadoFisico = fila.enumeracion("estado_fisico", EstadoFisicoPoste.BUENO) { EstadoFisicoPoste.valueOf(it) },
            observaciones = fila.textoONulo("observaciones"),
            operacionPendiente = OperacionPendiente.NINGUNA,
        )
    }

    fun filaATramoRed(fila: Map<String, Any?>, sectorTrabajoId: Long): TramoRed {
        return TramoRed(
            globalId = fila.textoOGenerar(COL_GLOBAL_ID),
            sectorTrabajoId = sectorTrabajoId,
            geometria = fila.geometriaLinea(),
            tipoRed = fila.enumeracion("tipo_red", TipoRed.OTRO) { TipoRed.valueOf(it) },
            longitudM = fila.decimalONulo("longitud_m"),
            estado = fila.enumeracion("estado", EstadoTramoRed.ACTIVA) { EstadoTramoRed.valueOf(it) },
            operacionPendiente = OperacionPendiente.NINGUNA,
        )
    }

    fun filaAEquipo(fila: Map<String, Any?>): EquipoTelecomunicacion {
        return EquipoTelecomunicacion(
            globalId = fila.textoOGenerar(COL_GLOBAL_ID),
            geometria = fila.geometriaPuntoONula(),
            tipoEquipo = fila.enumeracion("tipo_equipo", TipoEquipo.OTRO) { TipoEquipo.valueOf(it) },
            marca = fila.textoONulo("marca"),
            modelo = fila.textoONulo("modelo"),
            numeroSerie = fila.textoONulo("numero_serie"),
            fechaInstalacion = fila.textoONulo("fecha_instalacion")?.let(LocalDate::parse),
            estado = fila.enumeracion("estado", EstadoEquipo.OPERATIVO) { EstadoEquipo.valueOf(it) },
            operacionPendiente = OperacionPendiente.NINGUNA,
        )
    }

    private fun Map<String, Any?>.texto(columna: String): String = this[columna] as? String
        ?: error("Columna '$columna' ausente o no es texto en la fila de réplica: $this")

    private fun Map<String, Any?>.textoONulo(columna: String): String? = this[columna] as? String

    private fun Map<String, Any?>.textoOGenerar(columna: String): String =
        this[columna] as? String ?: UUID.randomUUID().toString()

    private fun Map<String, Any?>.decimalONulo(columna: String): Double? = (this[columna] as? Number)?.toDouble()

    private fun Map<String, Any?>.enteroONulo(columna: String): Int? = (this[columna] as? Number)?.toInt()

    private fun <T : Enum<T>> Map<String, Any?>.enumeracion(
        columna: String,
        porDefecto: T,
        valorDe: (String) -> T,
    ): T = (this[columna] as? String)?.let { runCatching { valorDe(it.uppercase()) }.getOrDefault(porDefecto) }
        ?: porDefecto

    private fun Map<String, Any?>.geometriaPunto(): Point =
        geometriaPuntoONula() ?: error("Columna '$COL_SHAPE' ausente para geometría de tipo punto: $this")

    private fun Map<String, Any?>.geometriaPuntoONula(): Point? =
        (this[COL_SHAPE] as? ByteArray)?.let { GeometryReader.readGeometry(it) as Point }

    private fun Map<String, Any?>.geometriaLinea(): LineString =
        (this[COL_SHAPE] as? ByteArray)?.let { GeometryReader.readGeometry(it) as LineString }
            ?: error("Columna '$COL_SHAPE' ausente para geometría de tipo línea: $this")
}
