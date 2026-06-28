package ec.cnel.sgaie.movil.map

import android.database.sqlite.SQLiteDatabase
import fi.iki.elonen.NanoHTTPD
import java.io.File

/**
 * Servidor HTTP embebido que expone un paquete .mbtiles (descargado para un
 * sector_trabajo, ver mobile/ESPECIFICACION_MOVIL_OFFLINE.md §6) como tiles
 * raster XYZ en 127.0.0.1, para que MapLibre los consuma vía un RasterSource
 * http(s) normal sin necesitar acceso a Internet.
 *
 * MBTiles almacena las filas en convención TMS (Y invertido respecto a XYZ),
 * de ahí la conversión `tmsY = (2^z - 1) - y` en cada solicitud.
 */
class OfflineTileServer(
    private val mbtilesFile: File,
    port: Int = DEFAULT_PORT,
) : NanoHTTPD(LOCAL_HOST, port) {

    private val db: SQLiteDatabase by lazy {
        SQLiteDatabase.openDatabase(mbtilesFile.path, null, SQLiteDatabase.OPEN_READONLY)
    }

    fun tileUrlTemplate(): String = "http://$LOCAL_HOST:$listeningPort/tiles/{z}/{x}/{y}.png"

    override fun serve(session: IHTTPSession): Response {
        val partes = session.uri.trim('/').split('/')
        if (partes.size != 4 || partes[0] != "tiles") {
            return newFixedLengthResponse(Response.Status.NOT_FOUND, "text/plain", "ruta no soportada")
        }

        val z = partes[1].toIntOrNull()
        val x = partes[2].toIntOrNull()
        val y = partes[3].removeSuffix(".png").toIntOrNull()
        if (z == null || x == null || y == null) {
            return newFixedLengthResponse(Response.Status.BAD_REQUEST, "text/plain", "z/x/y inválidos")
        }

        val tmsY = (1 shl z) - 1 - y
        val tile = leerTile(z, x, tmsY)
            ?: return newFixedLengthResponse(Response.Status.NOT_FOUND, "text/plain", "tile no disponible")

        return newFixedLengthResponse(Response.Status.OK, "image/png", tile.inputStream(), tile.size.toLong())
    }

    private fun leerTile(z: Int, x: Int, tmsY: Int): ByteArray? {
        val cursor = db.rawQuery(
            "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
            arrayOf(z.toString(), x.toString(), tmsY.toString()),
        )
        return cursor.use {
            if (it.moveToFirst()) it.getBlob(0) else null
        }
    }

    companion object {
        private const val LOCAL_HOST = "127.0.0.1"
        private const val DEFAULT_PORT = 8765
    }
}
