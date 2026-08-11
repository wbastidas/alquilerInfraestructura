package ec.cnel.sgaie.movil.sync

import ec.cnel.sgaie.movil.data.ColaSincronizacionRepository
import ec.cnel.sgaie.movil.data.ConflictoSincronizacion
import ec.cnel.sgaie.movil.data.ConflictoSincronizacionRepository
import ec.cnel.sgaie.movil.data.EntidadTipo
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacion
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacionRepository
import ec.cnel.sgaie.movil.data.EstadoSectorTrabajo
import ec.cnel.sgaie.movil.data.EstadoSincronizacion
import ec.cnel.sgaie.movil.data.ItemColaSincronizacion
import ec.cnel.sgaie.movil.data.OperacionSincronizacion
import ec.cnel.sgaie.movil.data.Poste
import ec.cnel.sgaie.movil.data.PosteRepository
import ec.cnel.sgaie.movil.data.SectorTrabajoRepository
import ec.cnel.sgaie.movil.data.TablaOrigen
import ec.cnel.sgaie.movil.data.TipoConflictoSincronizacion
import ec.cnel.sgaie.movil.data.TramoRed
import ec.cnel.sgaie.movil.data.TramoRedRepository
import mil.nga.sf.LineString
import mil.nga.sf.Point
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * §5.3/§5.4: orquestador de subida de cambios. Drena `cola_sincronizacion`
 * (PENDIENTE), agrupa por [TablaOrigen] y sube cada grupo con
 * `ArcGisRestClient.applyEdits` a la capa correspondiente
 * (`ArcGisConfig.Capas`), clasificando el resultado por feature en
 * ENVIADO/ERROR/CONFLICTO.
 *
 * Alcance explícito: solo POSTE/TRAMO_RED/EQUIPO tienen capa confirmada en
 * `ArcGisConfig.Capas`. `NOTA_INCUMPLIMIENTO`/`NOTA_ACEPTACION_RUTA` no
 * tienen Feature Service de destino confirmado — sus ítems quedan
 * `PENDIENTE` sin tocar (gap explícito pendiente de CNEL EP, §13). Las
 * `FOTOGRAFIA` se suben como adjunto (`addAttachment`) solo cuando están
 * vinculadas a una entidad POSTE/TRAMO_RED/EQUIPO con OBJECTID resoluble en
 * el servidor; fotos de SECTOR/NOTA_* quedan igualmente `PENDIENTE`.
 */
class SincronizadorCambios(
    private val client: ArcGisRestClient,
    private val cola: ColaSincronizacionRepository,
    private val conflictos: ConflictoSincronizacionRepository,
    private val sectores: SectorTrabajoRepository,
    private val postes: PosteRepository,
    private val tramos: TramoRedRepository,
    private val equipos: EquipoTelecomunicacionRepository,
) {
    data class Resultado(
        val enviados: Int = 0,
        val errores: Int = 0,
        val conflictos: Int = 0,
        val omitidos: Int = 0,
    )

    fun sincronizar(): Resultado {
        val pendientes = cola.listarPendientes()

        val resultadoPoste = procesarPoste(pendientes.filter { it.tablaOrigen == TablaOrigen.POSTE })
        val resultadoTramo = procesarTramo(pendientes.filter { it.tablaOrigen == TablaOrigen.TRAMO_RED })
        val resultadoEquipo = procesarEquipo(pendientes.filter { it.tablaOrigen == TablaOrigen.EQUIPO })
        val resultadoFoto = procesarFotografias(pendientes.filter { it.tablaOrigen == TablaOrigen.FOTOGRAFIA })
        val omitidasNotas = pendientes.count {
            it.tablaOrigen == TablaOrigen.NOTA_INCUMPLIMIENTO || it.tablaOrigen == TablaOrigen.NOTA_ACEPTACION_RUTA
        }

        recomputarEstadosSector()

        return Resultado(
            enviados = resultadoPoste.enviados + resultadoTramo.enviados + resultadoEquipo.enviados + resultadoFoto.enviados,
            errores = resultadoPoste.errores + resultadoTramo.errores + resultadoEquipo.errores + resultadoFoto.errores,
            conflictos = resultadoPoste.conflictos + resultadoTramo.conflictos + resultadoEquipo.conflictos,
            omitidos = resultadoFoto.omitidos + omitidasNotas,
        )
    }

    private fun procesarPoste(items: List<ItemColaSincronizacion>): Resultado {
        if (items.isEmpty()) return Resultado()
        val adds = mutableListOf<JSONObject>()
        val updates = mutableListOf<JSONObject>()
        val deletes = mutableListOf<String>()
        val itemPorGlobalId = mutableMapOf<String, ItemColaSincronizacion>()
        var erroresLocales = 0

        for (item in items) {
            val payload = JSONObject(item.payloadJson)
            val globalId = payload.getString("global_id")
            itemPorGlobalId[globalId] = item
            when (item.operacion) {
                OperacionSincronizacion.ELIMINAR -> deletes += globalId
                OperacionSincronizacion.CREAR, OperacionSincronizacion.EDITAR -> {
                    val poste = postes.obtenerPorId(item.entidadId)
                    if (poste == null) {
                        cola.marcarError(item.id, "El poste local ya no existe; no se puede subir el cambio.")
                        erroresLocales++
                        continue
                    }
                    val feature = JSONObject()
                        .put("attributes", posteAtributos(poste, globalId))
                        .put("geometry", poste.geometria.aEsriJson())
                    if (item.operacion == OperacionSincronizacion.CREAR) adds += feature else updates += feature
                }
            }
        }

        val respuesta = try {
            client.applyEdits(ArcGisConfig.Capas.POSTE, adds, updates, deletes)
        } catch (e: Exception) {
            items.forEach { cola.marcarError(it.id, "applyEdits falló: ${e.message}") }
            return Resultado(errores = items.size)
        }

        val parcial = procesarResultados(respuesta, itemPorGlobalId, TablaOrigen.POSTE)
        return parcial.copy(errores = parcial.errores + erroresLocales)
    }

    private fun procesarTramo(items: List<ItemColaSincronizacion>): Resultado {
        if (items.isEmpty()) return Resultado()
        val adds = mutableListOf<JSONObject>()
        val updates = mutableListOf<JSONObject>()
        val deletes = mutableListOf<String>()
        val itemPorGlobalId = mutableMapOf<String, ItemColaSincronizacion>()
        var erroresLocales = 0

        for (item in items) {
            val payload = JSONObject(item.payloadJson)
            val globalId = payload.getString("global_id")
            itemPorGlobalId[globalId] = item
            when (item.operacion) {
                OperacionSincronizacion.ELIMINAR -> deletes += globalId
                OperacionSincronizacion.CREAR, OperacionSincronizacion.EDITAR -> {
                    val tramo = tramos.obtenerPorId(item.entidadId)
                    if (tramo == null) {
                        cola.marcarError(item.id, "El tramo local ya no existe; no se puede subir el cambio.")
                        erroresLocales++
                        continue
                    }
                    val feature = JSONObject()
                        .put("attributes", tramoAtributos(tramo, globalId))
                        .put("geometry", tramo.geometria.aEsriJson())
                    if (item.operacion == OperacionSincronizacion.CREAR) adds += feature else updates += feature
                }
            }
        }

        val respuesta = try {
            client.applyEdits(ArcGisConfig.Capas.TRAMO_RED, adds, updates, deletes)
        } catch (e: Exception) {
            items.forEach { cola.marcarError(it.id, "applyEdits falló: ${e.message}") }
            return Resultado(errores = items.size)
        }

        val parcial = procesarResultados(respuesta, itemPorGlobalId, TablaOrigen.TRAMO_RED)
        return parcial.copy(errores = parcial.errores + erroresLocales)
    }

    private fun procesarEquipo(items: List<ItemColaSincronizacion>): Resultado {
        if (items.isEmpty()) return Resultado()
        val adds = mutableListOf<JSONObject>()
        val updates = mutableListOf<JSONObject>()
        val deletes = mutableListOf<String>()
        val itemPorGlobalId = mutableMapOf<String, ItemColaSincronizacion>()
        var erroresLocales = 0

        for (item in items) {
            val payload = JSONObject(item.payloadJson)
            val globalId = payload.getString("global_id")
            itemPorGlobalId[globalId] = item
            when (item.operacion) {
                OperacionSincronizacion.ELIMINAR -> deletes += globalId
                OperacionSincronizacion.CREAR, OperacionSincronizacion.EDITAR -> {
                    val equipo = equipos.obtenerPorId(item.entidadId)
                    if (equipo == null) {
                        cola.marcarError(item.id, "El equipo local ya no existe; no se puede subir el cambio.")
                        erroresLocales++
                        continue
                    }
                    val feature = JSONObject().put("attributes", equipoAtributos(equipo, globalId))
                    equipo.geometria?.let { feature.put("geometry", it.aEsriJson()) }
                    if (item.operacion == OperacionSincronizacion.CREAR) adds += feature else updates += feature
                }
            }
        }

        val respuesta = try {
            client.applyEdits(ArcGisConfig.Capas.EQUIPO_TELECOMUNICACION, adds, updates, deletes)
        } catch (e: Exception) {
            items.forEach { cola.marcarError(it.id, "applyEdits falló: ${e.message}") }
            return Resultado(errores = items.size)
        }

        val parcial = procesarResultados(respuesta, itemPorGlobalId, TablaOrigen.EQUIPO)
        return parcial.copy(errores = parcial.errores + erroresLocales)
    }

    /**
     * Interpreta `addResults`/`updateResults`/`deleteResults` de `applyEdits`
     * (cada entrada con `globalId`/`success`/`error`) y clasifica cada
     * rechazo en CONFLICTO (§5.4, revisión manual obligatoria) o ERROR
     * (reintentable). `# NOTA: la distinción se hace por texto del mensaje de
     * ArcGIS ("not found"/"no encontr..."), no se pudo confirmar el código de
     * error exacto contra un Feature Service real de CNEL EP en este sandbox
     * (§13); ajustar si el servicio real usa otro código/mensaje.`
     */
    private fun procesarResultados(
        respuesta: JSONObject,
        itemPorGlobalId: Map<String, ItemColaSincronizacion>,
        tablaOrigen: TablaOrigen,
    ): Resultado {
        var enviados = 0
        var errores = 0
        var conflictosNuevos = 0

        for (clave in listOf("addResults", "updateResults", "deleteResults")) {
            val resultados = respuesta.optJSONArray(clave) ?: continue
            for (i in 0 until resultados.length()) {
                val resultado = resultados.getJSONObject(i)
                val globalId = resultado.optString("globalId").ifEmpty { resultado.optString("globalID") }
                val item = itemPorGlobalId[globalId] ?: continue

                if (resultado.optBoolean("success")) {
                    cola.marcarEnviado(item.id)
                    enviados++
                    continue
                }

                val error = resultado.optJSONObject("error")
                val descripcion = (error?.optString("description").orEmpty())
                    .ifEmpty { error?.optString("message").orEmpty() }
                    .ifEmpty { "applyEdits rechazó el cambio." }

                if (descripcion.contains("not found", ignoreCase = true) ||
                    descripcion.contains("no encontr", ignoreCase = true)
                ) {
                    cola.marcarConflicto(item.id, descripcion)
                    conflictos.insertar(
                        ConflictoSincronizacion(
                            colaSincronizacionId = item.id,
                            tablaOrigen = tablaOrigen,
                            entidadId = item.entidadId,
                            tipo = TipoConflictoSincronizacion.ELIMINADO_EN_SERVIDOR,
                            payloadLocalJson = item.payloadJson,
                            payloadServidorJson = null,
                            mensaje = descripcion,
                        ),
                    )
                    conflictosNuevos++
                } else {
                    cola.marcarError(item.id, descripcion)
                    errores++
                }
            }
        }

        return Resultado(enviados = enviados, errores = errores, conflictos = conflictosNuevos)
    }

    /**
     * Sube fotos como adjunto de su entidad relacionada (§5.3/M4). Requiere
     * resolver el OBJECTID remoto vía el `global_id` de la entidad
     * POSTE/TRAMO_RED/EQUIPO asociada; si esa entidad aún no tiene OBJECTID
     * (no se ha sincronizado ella misma todavía), la foto se reintenta en el
     * próximo ciclo sin marcar error.
     */
    private fun procesarFotografias(items: List<ItemColaSincronizacion>): Resultado {
        var enviados = 0
        var errores = 0
        var omitidos = 0

        for (item in items) {
            val payload = JSONObject(item.payloadJson)
            val entidadTipo = EntidadTipo.valueOf(payload.getString("entidad_tipo"))
            val entidadIdRelacionada = payload.getLong("entidad_id")
            val layerId = capaPorEntidadTipo(entidadTipo)
            if (layerId == null) {
                omitidos++
                continue
            }

            val globalIdEntidad = globalIdDeEntidad(entidadTipo, entidadIdRelacionada)
            if (globalIdEntidad == null) {
                cola.marcarError(item.id, "La entidad asociada (poste/tramo/equipo) ya no existe localmente.")
                errores++
                continue
            }

            val objectId = try {
                client.obtenerObjectIdPorGlobalId(layerId, globalIdEntidad)
            } catch (e: Exception) {
                cola.marcarError(item.id, "No se pudo resolver el OBJECTID remoto: ${e.message}")
                errores++
                continue
            }
            if (objectId == null) continue

            try {
                client.addAttachment(layerId, objectId, File(payload.getString("ruta_archivo_local")))
                cola.marcarEnviado(item.id)
                enviados++
            } catch (e: Exception) {
                cola.marcarError(item.id, "addAttachment falló: ${e.message}")
                errores++
            }
        }

        return Resultado(enviados = enviados, errores = errores, omitidos = omitidos)
    }

    private fun capaPorEntidadTipo(entidadTipo: EntidadTipo): Int? = when (entidadTipo) {
        EntidadTipo.POSTE -> ArcGisConfig.Capas.POSTE
        EntidadTipo.TRAMO_RED -> ArcGisConfig.Capas.TRAMO_RED
        EntidadTipo.EQUIPO -> ArcGisConfig.Capas.EQUIPO_TELECOMUNICACION
        EntidadTipo.SECTOR, EntidadTipo.NOTA_INCUMPLIMIENTO, EntidadTipo.NOTA_ACEPTACION_RUTA -> null
    }

    private fun globalIdDeEntidad(entidadTipo: EntidadTipo, entidadId: Long): String? = when (entidadTipo) {
        EntidadTipo.POSTE -> postes.obtenerPorId(entidadId)?.globalId
        EntidadTipo.TRAMO_RED -> tramos.obtenerPorId(entidadId)?.globalId
        EntidadTipo.EQUIPO -> equipos.obtenerPorId(entidadId)?.globalId
        else -> null
    }

    /** `GlobalID`/`Shape` son los nombres de campo especiales de Esri; el resto sigue la convención en español del propio modelo (§4), igual que [FieldMapping]. */
    private fun posteAtributos(poste: Poste, globalId: String): JSONObject = JSONObject()
        .put("GlobalID", globalId)
        .put("codigo_poste", poste.codigoPoste)
        .put("tipo_poste", poste.tipoPoste.name)
        .put("altura_m", poste.alturaM)
        .put("capacidad_cables", poste.capacidadCables)
        .put("estado_fisico", poste.estadoFisico.name)
        .put("fecha_inspeccion", poste.fechaInspeccion?.toString())
        .put("observaciones", poste.observaciones)

    /**
     * `poste_origen_id`/`poste_destino_id` son ids locales (FK dentro del
     * GeoPackage del dispositivo) sin equivalente confirmado en el esquema de
     * ArcGIS; no se suben (`# TODO: confirmar con CNEL EP si la capa de
     * tramos tiene campos de relación con postes, §13`).
     */
    private fun tramoAtributos(tramo: TramoRed, globalId: String): JSONObject = JSONObject()
        .put("GlobalID", globalId)
        .put("tipo_red", tramo.tipoRed.name)
        .put("longitud_m", tramo.longitudM)
        .put("estado", tramo.estado.name)

    /** `poste_id` es un id local sin equivalente confirmado en ArcGIS; no se sube (mismo motivo que [tramoAtributos]). */
    private fun equipoAtributos(equipo: EquipoTelecomunicacion, globalId: String): JSONObject = JSONObject()
        .put("GlobalID", globalId)
        .put("tipo_equipo", equipo.tipoEquipo.name)
        .put("marca", equipo.marca)
        .put("modelo", equipo.modelo)
        .put("numero_serie", equipo.numeroSerie)
        .put("fecha_instalacion", equipo.fechaInstalacion?.toString())
        .put("estado", equipo.estado.name)

    private fun Point.aEsriJson(): JSONObject = JSONObject()
        .put("x", x)
        .put("y", y)
        .put("spatialReference", JSONObject().put("wkid", 4326))

    private fun LineString.aEsriJson(): JSONObject {
        val path = JSONArray()
        points.forEach { punto -> path.put(JSONArray().put(punto.x).put(punto.y)) }
        return JSONObject()
            .put("paths", JSONArray().put(path))
            .put("spatialReference", JSONObject().put("wkid", 4326))
    }

    /**
     * Tras procesar la cola, recalcula `sector_trabajo.estado` (§5.3/§5.4):
     * `CON_CONFLICTOS` si queda algún ítem `CONFLICTO` asociado al sector,
     * `SINCRONIZADO` si ya no queda ningún ítem `PENDIENTE`/`ERROR`/`CONFLICTO`,
     * o sin cambios si todavía hay ítems por reintentar.
     */
    private fun recomputarEstadosSector() {
        val todos = cola.listarTodos()
        val sectorPorItem = todos.associateWith { resolverSectorTrabajoId(it) }
        val sectoresAfectados = sectorPorItem.values.filterNotNull().toSet()

        for (sectorId in sectoresAfectados) {
            val itemsSector = sectorPorItem.filterValues { it == sectorId }.keys
            val tieneConflicto = itemsSector.any { it.estado == EstadoSincronizacion.CONFLICTO }
            val tienePendiente = itemsSector.any {
                it.estado == EstadoSincronizacion.PENDIENTE || it.estado == EstadoSincronizacion.ERROR
            }
            when {
                tieneConflicto -> sectores.actualizarEstado(sectorId, EstadoSectorTrabajo.CON_CONFLICTOS)
                !tienePendiente -> sectores.actualizarEstado(sectorId, EstadoSectorTrabajo.SINCRONIZADO)
                else -> Unit
            }
        }
    }

    /**
     * Resuelve a qué sector pertenece un ítem de la cola para recalcular su
     * estado. POSTE/TRAMO_RED/NOTA_ACEPTACION_RUTA llevan `sector_trabajo_id`
     * directo en su payload; EQUIPO solo lleva `poste_id`, así que se
     * resuelve indirectamente vía el poste local (si todavía existe).
     * NOTA_INCUMPLIMIENTO/FOTOGRAFIA no se resuelven (mismo gap ya
     * documentado en la clase).
     */
    private fun resolverSectorTrabajoId(item: ItemColaSincronizacion): Long? = when (item.tablaOrigen) {
        TablaOrigen.POSTE, TablaOrigen.TRAMO_RED, TablaOrigen.NOTA_ACEPTACION_RUTA ->
            runCatching { JSONObject(item.payloadJson).getLong("sector_trabajo_id") }.getOrNull()
        TablaOrigen.EQUIPO -> runCatching {
            val posteId = JSONObject(item.payloadJson).optLong("poste_id", -1).takeIf { it >= 0 }
            posteId?.let { postes.obtenerPorId(it)?.sectorTrabajoId }
        }.getOrNull()
        TablaOrigen.NOTA_INCUMPLIMIENTO, TablaOrigen.FOTOGRAFIA -> null
    }
}
