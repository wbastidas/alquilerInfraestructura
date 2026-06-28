package ec.cnel.sgaie.movil.map

import android.Manifest
import android.content.pm.PackageManager
import android.location.Location
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.weight
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.exifinterface.media.ExifInterface
import ec.cnel.sgaie.movil.data.EntidadTipo
import ec.cnel.sgaie.movil.data.Fotografia
import ec.cnel.sgaie.movil.data.FotografiaRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest
import java.util.UUID

/**
 * Dominio §4.7/§7: captura de una fotografía geolocalizada vinculada a la
 * entidad indicada (poste/tramo/equipo/nota), con metadata EXIF GPS y hash
 * de integridad SHA-256, encolada para sync igual que el resto de M3 (§5.2).
 *
 * `# TODO: acimut_grados (orientación de la cámara, §4.7) no se captura en
 * este pase — requeriría fusión de sensores (acelerómetro+magnetómetro) que
 * no se puede verificar sin compilar/probar en un dispositivo real (§13).`
 */
@Composable
fun FotografiaCapturaScreen(
    entidadTipo: EntidadTipo,
    entidadId: Long,
    onFinalizado: () -> Unit,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()
    val repository = remember { FotografiaRepository(context) }

    var permisosConcedidos by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED,
        )
    }
    val lanzadorPermisos = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { resultados ->
        permisosConcedidos = resultados.values.all { it }
    }

    var capturaImagen by remember { mutableStateOf<ImageCapture?>(null) }
    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var ultimaFotoGuardada by remember { mutableStateOf(false) }

    if (!permisosConcedidos) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(text = "Se requiere acceso a la cámara y la ubicación para tomar fotografías geolocalizadas.")
            Button(onClick = {
                lanzadorPermisos.launch(arrayOf(Manifest.permission.CAMERA, Manifest.permission.ACCESS_FINE_LOCATION))
            }) { Text("Conceder permisos") }
            OutlinedButton(onClick = onFinalizado) { Text("Cancelar") }
        }
        return
    }

    if (ultimaFotoGuardada) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(text = "Fotografía guardada y encolada para sincronización.")
            Button(onClick = { ultimaFotoGuardada = false }) { Text("Tomar otra foto") }
            OutlinedButton(onClick = onFinalizado) { Text("Finalizar") }
        }
        return
    }

    Column(modifier = Modifier.fillMaxSize()) {
        AndroidView(
            modifier = Modifier.fillMaxWidth().weight(1f),
            factory = { ctx ->
                val previewView = PreviewView(ctx)
                val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                cameraProviderFuture.addListener({
                    val cameraProvider = cameraProviderFuture.get()
                    val preview = Preview.Builder().build().also {
                        it.setSurfaceProvider(previewView.surfaceProvider)
                    }
                    val imageCapture = ImageCapture.Builder().build()
                    runCatching {
                        cameraProvider.unbindAll()
                        cameraProvider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, imageCapture)
                    }
                    capturaImagen = imageCapture
                }, ContextCompat.getMainExecutor(ctx))
                previewView
            },
        )

        error?.let { Text(text = it, modifier = Modifier.padding(16.dp)) }

        Column(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (enProgreso) {
                CircularProgressIndicator()
            } else {
                Button(onClick = {
                    val imageCapture = capturaImagen
                    if (imageCapture == null) {
                        error = "La cámara aún no está lista."
                        return@Button
                    }
                    error = null
                    enProgreso = true
                    val archivoDestino = File(
                        context.getExternalFilesDir("fotografias"),
                        "foto_${System.currentTimeMillis()}.jpg",
                    )
                    archivoDestino.parentFile?.mkdirs()
                    val opciones = ImageCapture.OutputFileOptions.Builder(archivoDestino).build()
                    imageCapture.takePicture(
                        opciones,
                        ContextCompat.getMainExecutor(context),
                        object : ImageCapture.OnImageSavedCallback {
                            override fun onImageSaved(salida: ImageCapture.OutputFileResults) {
                                scope.launch {
                                    try {
                                        val ubicacion = withContext(Dispatchers.IO) { obtenerUbicacionActual(context) }
                                        if (ubicacion == null) {
                                            error = "No se pudo obtener la ubicación actual."
                                            enProgreso = false
                                            return@launch
                                        }
                                        withContext(Dispatchers.IO) { escribirExifGps(archivoDestino, ubicacion) }
                                        val hash = withContext(Dispatchers.IO) { calcularHashSha256(archivoDestino) }
                                        withContext(Dispatchers.IO) {
                                            repository.insertar(
                                                Fotografia(
                                                    globalId = UUID.randomUUID().toString(),
                                                    entidadTipo = entidadTipo,
                                                    entidadId = entidadId,
                                                    rutaArchivoLocal = archivoDestino.absolutePath,
                                                    latitud = ubicacion.latitude,
                                                    longitud = ubicacion.longitude,
                                                    altitudM = if (ubicacion.hasAltitude()) ubicacion.altitude else null,
                                                    precisionGpsM = if (ubicacion.hasAccuracy()) ubicacion.accuracy.toDouble() else null,
                                                    acimutGrados = null,
                                                    hashSha256 = hash,
                                                ),
                                            )
                                        }
                                        enProgreso = false
                                        ultimaFotoGuardada = true
                                    } catch (excepcion: Exception) {
                                        error = "No se pudo guardar la fotografía: ${excepcion.message}"
                                        enProgreso = false
                                    }
                                }
                            }

                            override fun onError(excepcionCaptura: ImageCaptureException) {
                                error = "Error al capturar la fotografía: ${excepcionCaptura.message}"
                                enProgreso = false
                            }
                        },
                    )
                }) { Text("Capturar foto") }

                OutlinedButton(onClick = onFinalizado) { Text("Cancelar") }
            }
        }
    }
}

private fun escribirExifGps(archivo: File, ubicacion: Location) {
    val exif = ExifInterface(archivo.absolutePath)
    exif.setLatLong(ubicacion.latitude, ubicacion.longitude)
    if (ubicacion.hasAltitude()) {
        exif.setAltitude(ubicacion.altitude)
    }
    if (ubicacion.hasAccuracy()) {
        exif.setAttribute(ExifInterface.TAG_GPS_H_POSITIONING_ERROR, ubicacion.accuracy.toString())
    }
    exif.saveAttributes()
}

private fun calcularHashSha256(archivo: File): String {
    val digest = MessageDigest.getInstance("SHA-256")
    archivo.inputStream().use { entrada ->
        val buffer = ByteArray(8192)
        var leidos: Int
        while (entrada.read(buffer).also { leidos = it } != -1) {
            digest.update(buffer, 0, leidos)
        }
    }
    return digest.digest().joinToString("") { "%02x".format(it) }
}
