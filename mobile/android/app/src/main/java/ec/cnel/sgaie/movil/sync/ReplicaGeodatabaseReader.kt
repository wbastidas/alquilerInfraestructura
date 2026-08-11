package ec.cnel.sgaie.movil.sync

import android.database.sqlite.SQLiteDatabase
import java.io.File

/**
 * Abre el `.geodatabase` de réplica descargado por [ArcGisRestClient] — con
 * `dataFormat=sqlite` la réplica de ArcGIS es directamente un archivo
 * SQLite, sin necesidad de un parser de geodatabase binaria propietario.
 *
 * Expone filas crudas (`Map<columna, valor>`) por nombre de tabla/capa, sin
 * asumir nombres de columna: el mapeo a las entidades GeoPackage locales lo
 * hace [FieldMapping] por separado, porque el esquema real de capas de CNEL
 * EP está pendiente de confirmación (§13).
 */
class ReplicaGeodatabaseReader(archivo: File) : AutoCloseable {

    private val db: SQLiteDatabase =
        SQLiteDatabase.openDatabase(archivo.path, null, SQLiteDatabase.OPEN_READONLY)

    fun nombresDeTablas(): List<String> {
        val nombres = mutableListOf<String>()
        db.rawQuery(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'gdb_%'",
            null,
        ).use { cursor ->
            while (cursor.moveToNext()) {
                nombres += cursor.getString(0)
            }
        }
        return nombres
    }

    fun filasDeTabla(nombreTabla: String): List<Map<String, Any?>> {
        val filas = mutableListOf<Map<String, Any?>>()
        db.rawQuery("SELECT * FROM \"$nombreTabla\"", null).use { cursor ->
            while (cursor.moveToNext()) {
                val fila = mutableMapOf<String, Any?>()
                for (i in 0 until cursor.columnCount) {
                    fila[cursor.getColumnName(i)] = when (cursor.getType(i)) {
                        android.database.Cursor.FIELD_TYPE_INTEGER -> cursor.getLong(i)
                        android.database.Cursor.FIELD_TYPE_FLOAT -> cursor.getDouble(i)
                        android.database.Cursor.FIELD_TYPE_BLOB -> cursor.getBlob(i)
                        android.database.Cursor.FIELD_TYPE_NULL -> null
                        else -> cursor.getString(i)
                    }
                }
                filas += fila
            }
        }
        return filas
    }

    override fun close() {
        db.close()
    }
}
