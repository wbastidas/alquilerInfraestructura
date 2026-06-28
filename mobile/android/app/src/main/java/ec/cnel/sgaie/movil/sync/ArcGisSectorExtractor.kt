package ec.cnel.sgaie.movil.sync

import android.content.Context
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacionRepository
import ec.cnel.sgaie.movil.data.PosteRepository
import ec.cnel.sgaie.movil.data.SectorTrabajo
import ec.cnel.sgaie.movil.data.SectorTrabajoRepository
import ec.cnel.sgaie.movil.data.TramoRedRepository
import java.io.File

/**
 * Orquesta la extracción M2 completa de un sector de trabajo (§5.1):
 * `createReplica` (ArcGIS) -> descarga -> lectura de la réplica SQLite ->
 * mapeo de campos ([FieldMapping]) -> escritura en los repositorios
 * GeoPackage locales.
 *
 * Resuelve además las referencias entre capas (poste de origen/destino de un
 * tramo, poste de un equipo): [FieldMapping] traduce cada fila de forma
 * aislada y no puede conocer el id local (autoincremental) que el poste
 * referenciado recibirá al insertarse, así que esta clase construye, a
 * medida que inserta los postes del sector, un mapa GlobalID -> id local
 * para resolver esas referencias antes de insertar tramos y equipos.
 *
 * `# TODO: confirmar contra el servicio real de CNEL EP los nombres de tabla
 * por capa dentro de la réplica, y que las columnas de relación
 * poste_origen_id/poste_destino_id/poste_id efectivamente contengan el
 * GlobalID (texto) del poste relacionado y no su OBJECTID numérico -- ambas
 * son convenciones posibles de un Feature Service con relaciones por
 * GlobalID (§13).`
 */
class ArcGisSectorExtractor(
    context: Context,
    private val restClient: ArcGisRestClient,
) {

    private val sectorTrabajoRepository = SectorTrabajoRepository(context)
    private val posteRepository = PosteRepository(context)
    private val tramoRedRepository = TramoRedRepository(context)
    private val equipoRepository = EquipoTelecomunicacionRepository(context)

    /**
     * Descarga y persiste localmente el sector [sector] (sin id local todavía)
     * dentro del [envelope] indicado, usando [archivoTemporal] como destino de
     * la réplica descargada. Devuelve el [SectorTrabajo] ya persistido, con su
     * id local asignado.
     */
    fun extraer(sector: SectorTrabajo, envelope: Envelope, archivoTemporal: File): SectorTrabajo {
        val sectorTrabajoId = sectorTrabajoRepository.insertar(sector)

        val replica = restClient.createReplica(
            nombreReplica = sector.codigo,
            capas = listOf(
                ArcGisConfig.Capas.POSTE,
                ArcGisConfig.Capas.TRAMO_RED,
                ArcGisConfig.Capas.EQUIPO_TELECOMUNICACION,
            ),
            envelope = envelope,
            destino = archivoTemporal,
        )

        ReplicaGeodatabaseReader(replica).use { lector ->
            val tablasPresentes = lector.nombresDeTablas().toSet()
            val idLocalPorGlobalIdPoste = mutableMapOf<String, Long>()

            if (TABLA_POSTE in tablasPresentes) {
                lector.filasDeTabla(TABLA_POSTE).forEach { fila ->
                    val poste = FieldMapping.filaAPoste(fila, sectorTrabajoId)
                    val idLocal = posteRepository.insertar(poste)
                    idLocalPorGlobalIdPoste[poste.globalId] = idLocal
                }
            }

            if (TABLA_TRAMO_RED in tablasPresentes) {
                lector.filasDeTabla(TABLA_TRAMO_RED).forEach { fila ->
                    val tramo = FieldMapping.filaATramoRed(fila, sectorTrabajoId).copy(
                        posteOrigenId = (fila[COL_POSTE_ORIGEN_ID] as? String)?.let(idLocalPorGlobalIdPoste::get),
                        posteDestinoId = (fila[COL_POSTE_DESTINO_ID] as? String)?.let(idLocalPorGlobalIdPoste::get),
                    )
                    tramoRedRepository.insertar(tramo)
                }
            }

            if (TABLA_EQUIPO_TELECOMUNICACION in tablasPresentes) {
                lector.filasDeTabla(TABLA_EQUIPO_TELECOMUNICACION).forEach { fila ->
                    val equipo = FieldMapping.filaAEquipo(fila).copy(
                        posteId = (fila[COL_POSTE_ID] as? String)?.let(idLocalPorGlobalIdPoste::get),
                    )
                    equipoRepository.insertar(equipo)
                }
            }
        }

        return sector.copy(id = sectorTrabajoId)
    }

    private companion object {
        const val TABLA_POSTE = "Poste"
        const val TABLA_TRAMO_RED = "TramoRed"
        const val TABLA_EQUIPO_TELECOMUNICACION = "EquipoTelecomunicacion"
        const val COL_POSTE_ORIGEN_ID = "poste_origen_id"
        const val COL_POSTE_DESTINO_ID = "poste_destino_id"
        const val COL_POSTE_ID = "poste_id"
    }
}
