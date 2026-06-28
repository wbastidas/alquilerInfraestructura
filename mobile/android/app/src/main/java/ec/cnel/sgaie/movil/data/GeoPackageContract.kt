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
