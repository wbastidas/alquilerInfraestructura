package ec.cnel.sgaie.movil.sync

import android.content.Context
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import ec.cnel.sgaie.movil.data.ColaSincronizacionRepository
import ec.cnel.sgaie.movil.data.ConflictoSincronizacionRepository
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacionRepository
import ec.cnel.sgaie.movil.data.PosteRepository
import ec.cnel.sgaie.movil.data.SectorTrabajoRepository
import ec.cnel.sgaie.movil.data.TramoRedRepository
import java.util.concurrent.TimeUnit

/**
 * Sincronización periódica en segundo plano (M5, §5.3): reutiliza la misma
 * URL/token de la última sincronización manual en
 * [ec.cnel.sgaie.movil.map.SincronizacionScreen], persistidos en
 * [SincronizacionPreferencias]. Si el usuario nunca sincronizó manualmente al
 * menos una vez, no hay credenciales guardadas y el ciclo se omite
 * silenciosamente (`Result.success`) hasta que las haya.
 */
class SincronizacionWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val urlServicio = SincronizacionPreferencias.obtenerUrl(applicationContext) ?: return Result.success()
        val token = SincronizacionPreferencias.obtenerToken(applicationContext) ?: return Result.success()

        return try {
            val tokenProvider = ArcGisTokenProvider { token }
            val restClient = ArcGisRestClient(urlServicio, tokenProvider)
            val sincronizador = SincronizadorCambios(
                client = restClient,
                cola = ColaSincronizacionRepository(applicationContext),
                conflictos = ConflictoSincronizacionRepository(applicationContext),
                sectores = SectorTrabajoRepository(applicationContext),
                postes = PosteRepository(applicationContext),
                tramos = TramoRedRepository(applicationContext),
                equipos = EquipoTelecomunicacionRepository(applicationContext),
            )
            sincronizador.sincronizar()
            Result.success()
        } catch (excepcion: Exception) {
            Result.retry()
        }
    }

    companion object {
        private const val NOMBRE_WORK_PERIODICO = "sincronizacion_periodica"

        /**
         * 15 minutos es el mínimo permitido por WorkManager para trabajo
         * periódico; suficiente como cadencia de respaldo dado que la
         * sincronización manual (§5.3) sigue siendo el flujo principal.
         */
        fun programar(context: Context) {
            val restricciones = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val solicitud = PeriodicWorkRequestBuilder<SincronizacionWorker>(15, TimeUnit.MINUTES)
                .setConstraints(restricciones)
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                NOMBRE_WORK_PERIODICO,
                ExistingPeriodicWorkPolicy.KEEP,
                solicitud,
            )
        }
    }
}
