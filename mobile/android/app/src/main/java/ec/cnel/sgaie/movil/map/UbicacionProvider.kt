package ec.cnel.sgaie.movil.map

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.suspendCancellableCoroutine

/**
 * Dominio §7: "último fix de alta precisión disponible" para geolocalizar
 * una fotografía de campo. El llamador debe haber verificado ya el permiso
 * `ACCESS_FINE_LOCATION` en tiempo de ejecución.
 *
 * `# NOTA: la API de FusedLocationProviderClient/CancellationTokenSource no
 * se pudo verificar contra la versión real de play-services-location
 * resuelta en este entorno (§13/limitaciones), igual que el resto de la API
 * de bajo nivel usada en este scaffold.`
 */
@SuppressLint("MissingPermission")
suspend fun obtenerUbicacionActual(context: Context): Location? = suspendCancellableCoroutine { continuacion ->
    val cliente = LocationServices.getFusedLocationProviderClient(context)
    val cancelacion = CancellationTokenSource()
    continuacion.invokeOnCancellation { cancelacion.cancel() }
    cliente.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, cancelacion.token)
        .addOnSuccessListener { ubicacion -> continuacion.resumeWith(Result.success(ubicacion)) }
        .addOnFailureListener { continuacion.resumeWith(Result.success(null)) }
}
