package ec.cnel.sgaie.movil.sync

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Persiste la URL del Feature Service y el token capturados manualmente en
 * [ec.cnel.sgaie.movil.map.SincronizacionScreen], para que
 * [SincronizacionWorker] (sincronización periódica en segundo plano, M5,
 * §5.3) los reutilice sin pedírselos de nuevo al usuario.
 *
 * El archivo se cifra en reposo con `EncryptedSharedPreferences` (clave
 * maestra AES-256 en el Android Keystore), de modo que el token de ArcGIS no
 * quede legible ante acceso físico al almacenamiento del dispositivo.
 *
 * `# NOTA: si el Keystore falla (clave corrupta, restauración parcial del
 * sistema), se opta por "fail closed": guardar() descarta silenciosamente y
 * obtener*() devuelve null, con lo que el worker periódico simplemente se
 * omite hasta la próxima sincronización manual — nunca se degrada a
 * almacenamiento en claro. La captura manual de URL/token sigue siendo un
 * placeholder hasta tener login OAuth2 real (§9/§13).`
 */
object SincronizacionPreferencias {
    private const val PREFS_NOMBRE = "sincronizacion_config_segura"

    /** Nombre del archivo en claro usado por versiones previas del scaffold; se purga al guardar. */
    private const val PREFS_NOMBRE_ANTIGUO_EN_CLARO = "sincronizacion_config"
    private const val CLAVE_URL = "url_servicio"
    private const val CLAVE_TOKEN = "token"

    private fun prefs(context: Context): SharedPreferences {
        val claveMaestra = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        return EncryptedSharedPreferences.create(
            context,
            PREFS_NOMBRE,
            claveMaestra,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    fun guardar(context: Context, urlServicio: String, token: String) {
        context.deleteSharedPreferences(PREFS_NOMBRE_ANTIGUO_EN_CLARO)
        try {
            prefs(context)
                .edit()
                .putString(CLAVE_URL, urlServicio)
                .putString(CLAVE_TOKEN, token)
                .apply()
        } catch (excepcion: Exception) {
            // Fail closed: sin credenciales persistidas el worker se omite.
        }
    }

    fun obtenerUrl(context: Context): String? =
        try {
            prefs(context).getString(CLAVE_URL, null)
        } catch (excepcion: Exception) {
            null
        }

    fun obtenerToken(context: Context): String? =
        try {
            prefs(context).getString(CLAVE_TOKEN, null)
        } catch (excepcion: Exception) {
            null
        }
}
