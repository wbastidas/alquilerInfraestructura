package ec.cnel.sgaie.movil.data

/**
 * Nombres de tablas/columnas comunes del modelo GeoPackage local
 * (mobile/ESPECIFICACION_MOVIL_OFFLINE.md §4). Toda tabla de entidad de red
 * comparte estas columnas además de las propias.
 */
object GeoPackageContract {
    const val NOMBRE_ARCHIVO_DEFAULT = "sgaie-movil.gpkg"

    const val COL_ID = "id"
    const val COL_GLOBAL_ID = "global_id"
    const val COL_CREADO_EN = "creado_en"
    const val COL_ACTUALIZADO_EN = "actualizado_en"
    const val COL_OPERACION_PENDIENTE = "operacion_pendiente"

    const val TABLA_SECTOR_TRABAJO = "sector_trabajo"
    const val TABLA_POSTE = "poste"
    const val TABLA_TRAMO_RED = "tramo_red"
    const val TABLA_EQUIPO_TELECOMUNICACION = "equipo_telecomunicacion"
    const val TABLA_NOTA_INCUMPLIMIENTO = "nota_incumplimiento"
    const val TABLA_NOTA_ACEPTACION_RUTA = "nota_aceptacion_ruta"
    const val TABLA_FOTOGRAFIA = "fotografia"

    /** §4.9: no es tabla de feature (sin geometría), se modela como tabla de atributos (`UserTable` simple). */
    const val TABLA_COLA_SINCRONIZACION = "cola_sincronizacion"

    /** §5.4: registro de conflictos no resueltos automáticamente, igual de sin-geometría que la cola. */
    const val TABLA_CONFLICTO_SINCRONIZACION = "conflicto_sincronizacion"
}

/** Marca si un registro tiene cambios sin sincronizar (§4, encabezado). */
enum class OperacionPendiente {
    NINGUNA, CREAR, EDITAR, ELIMINAR
}

/** §4.1 `sector_trabajo.estado` */
enum class EstadoSectorTrabajo {
    DESCARGADO, EN_TRABAJO, PENDIENTE_SYNC, SINCRONIZADO, CON_CONFLICTOS
}

/** §4.2 `poste.tipo_poste` */
enum class TipoPoste {
    HORMIGON, MADERA, METALICO, OTRO
}

/** §4.2 `poste.estado_fisico` */
enum class EstadoFisicoPoste {
    BUENO, REGULAR, MALO, RETIRADO
}

/** §4.3 `tramo_red.tipo_red` (coincide con `tipo_redes` de Solicitud, §6.7 del backend) */
enum class TipoRed {
    FIBRA_OPTICA, COAXIAL, ELECTRICA, OTRO
}

/** §4.3 `tramo_red.estado` */
enum class EstadoTramoRed {
    ACTIVA, INACTIVA, RETIRADA
}

/** §4.4 `equipo_telecomunicacion.tipo_equipo` */
enum class TipoEquipo {
    SPLITTER, CAJA_EMPALME, AMPLIFICADOR, ONT, OTRO
}

/** §4.4 `equipo_telecomunicacion.estado` */
enum class EstadoEquipo {
    OPERATIVO, DANADO, RETIRADO
}

/** §4.5/§4.7: tipo de entidad referenciada polimórficamente (mismo patrón que `Documento.entidad_tipo` del backend, §6.8). */
enum class EntidadTipo {
    POSTE, TRAMO_RED, EQUIPO, SECTOR, NOTA_INCUMPLIMIENTO, NOTA_ACEPTACION_RUTA
}

/**
 * §4.5 `nota_incumplimiento.tipo_incumplimiento`. Catálogo sugerido por
 * defecto, no cerrado: `# TODO: confirmar catálogo cerrado con el área
 * normativa/MAPOD de CNEL EP (§13)`.
 */
enum class TipoIncumplimiento {
    EXCESO_CABLES_POSTE, CABLEADO_SIN_ORDEN, POSTE_MAL_ESTADO_ESTRUCTURAL,
    EQUIPO_SIN_AUTORIZACION, RUTA_FUERA_DE_LO_APROBADO, FALTA_SENALIZACION, OTRO
}

/** §4.5 `nota_incumplimiento.gravedad` */
enum class Gravedad {
    LEVE, MODERADA, GRAVE
}

/** §4.5 `nota_incumplimiento.estado_subsanacion` */
enum class EstadoSubsanacion {
    PENDIENTE, NOTIFICADO, SUBSANADO
}

/** §4.6 `nota_aceptacion_ruta.decision` */
enum class DecisionAceptacionRuta {
    ACEPTADA, ACEPTADA_CON_OBSERVACIONES, RECHAZADA
}

/** §4.9 `cola_sincronizacion.operacion` (coincide con `OperacionPendiente` sin el valor `NINGUNA`). */
enum class OperacionSincronizacion {
    CREAR, EDITAR, ELIMINAR
}

/**
 * §4.9 `cola_sincronizacion.estado`. `CONFLICTO` se agrega en M5 (§5.4) para
 * distinguir el único caso que la especificación exige dejar SIEMPRE para
 * revisión manual (elemento eliminado en el servidor mientras se editaba en
 * campo) de un `ERROR` simple y reintentable.
 */
enum class EstadoSincronizacion {
    PENDIENTE, ENVIADO, ERROR, CONFLICTO
}

/**
 * §4.9 `cola_sincronizacion.tabla_origen`: identifica la tabla GeoPackage que
 * generó el ítem encolado. Necesario porque `entidad_tipo`/`entidad_id` del
 * mismo ítem tienen semántica distinta según quién encola: para
 * poste/tramo_red/equipo, "esta fila ES esa entidad"; para
 * nota_incumplimiento/nota_aceptacion_ruta/fotografia, `entidad_tipo`/
 * `entidad_id` apuntan a la entidad SOBRE la que trata la nota/foto, no a la
 * nota/foto en sí (cuyo propio id local es el `entidad_id` original que ya
 * traía la fila). El sincronizador de M5 necesita saber esto último sin
 * ambigüedad para enrutar cada payload a la capa/tabla de ArcGIS correcta.
 */
enum class TablaOrigen {
    POSTE, TRAMO_RED, EQUIPO, NOTA_INCUMPLIMIENTO, NOTA_ACEPTACION_RUTA, FOTOGRAFIA
}

/**
 * §5.4: tipo de conflicto no resuelto automáticamente. `ELIMINADO_EN_SERVIDOR`
 * es el único caso que la especificación exige dejar siempre para revisión
 * manual; `ERROR_NO_RECUPERABLE` cubre cualquier otro rechazo de ArcGIS que,
 * tras los reintentos, no se puede aplicar sin intervención (p. ej. un
 * validation error de dominio que el campo no puede corregir solo).
 */
enum class TipoConflictoSincronizacion {
    ELIMINADO_EN_SERVIDOR, ERROR_NO_RECUPERABLE
}
