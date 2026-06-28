package ec.cnel.sgaie.movil.sync

import android.content.Context

/**
 * Persiste la URL del Feature Service y el token capturados manualmente en
 * [ec.cnel.sgaie.movil.map.SincronizacionScreen], para que
 * [SincronizacionWorker] (sincronización periódica en segundo plano, M5,
 * §5.3) los reutilice sin pedírselos de nuevo al usuario.
 *
 * `# TODO: igual que el resto de la captura manual de URL/token de este
 * scaffold, es un placeholder hasta tener login OAuth2 real (§9/§13); el
 * token queda en SharedPreferences sin cifrar, aceptable solo mientras dure
 * este enfoque temporal.`
 */
object SincronizacionPreferencias {
    private const val PREFS_NOMBRE = "sincronizacion_config"
    private const val CLAVE_URL = "url_servicio"
    private const val CLAVE_TOKEN = "token"

    fun guardar(context: Context, urlServicio: String, token: String) {
        context.getSharedPreferences(PREFS_NOMBRE, Context.MODE_PRIVATE)
            .edit()
            .putString(CLAVE_URL, urlServicio)
            .putString(CLAVE_TOKEN, token)
            .apply()
    }

    fun obtenerUrl(context: Context): String? =
        context.getSharedPreferences(PREFS_NOMBRE, Context.MODE_PRIVATE).getString(CLAVE_URL, null)

    fun obtenerToken(context: Context): String? =
        context.getSharedPreferences(PREFS_NOMBRE, Context.MODE_PRIVATE).getString(CLAVE_TOKEN, null)
}
