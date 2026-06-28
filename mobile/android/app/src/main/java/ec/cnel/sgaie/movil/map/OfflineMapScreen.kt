package ec.cnel.sgaie.movil.map

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import ec.cnel.sgaie.movil.R
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.Style
import java.io.File

/** Centro de cámara por defecto: Guayaquil (placeholder hasta tener sectores reales). */
private val CENTRO_POR_DEFECTO = LatLng(-2.1709979, -79.9223592)
private const val ZOOM_POR_DEFECTO = 12.0
private const val NOMBRE_MBTILES_DEMO = "sector-demo.mbtiles"

@Composable
fun OfflineMapScreen() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val mbtilesFile = remember {
        File(context.getExternalFilesDir("tiles"), NOMBRE_MBTILES_DEMO)
    }
    var tileServer by remember { mutableStateOf<OfflineTileServer?>(null) }

    if (!mbtilesFile.exists()) {
        Box(modifier = Modifier.fillMaxSize()) {
            Text(text = context.getString(R.string.mapa_sin_tiles))
        }
        return
    }

    val mapView = remember {
        MapView(context).apply { onCreate(null) }
    }

    DisposableEffect(lifecycleOwner) {
        val servidor = OfflineTileServer(mbtilesFile).also { it.start() }
        tileServer = servidor

        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> mapView.onStart()
                Lifecycle.Event.ON_RESUME -> mapView.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView.onPause()
                Lifecycle.Event.ON_STOP -> mapView.onStop()
                Lifecycle.Event.ON_DESTROY -> mapView.onDestroy()
                else -> Unit
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            servidor.stop()
        }
    }

    LaunchedEffect(tileServer) {
        val servidor = tileServer ?: return@LaunchedEffect
        val estiloJson = OfflineMapStyleProvider.construirEstiloJson(servidor.tileUrlTemplate())
        mapView.getMapAsync { mapa ->
            mapa.setStyle(Style.Builder().fromJson(estiloJson))
            mapa.cameraPosition = CameraPosition.Builder()
                .target(CENTRO_POR_DEFECTO)
                .zoom(ZOOM_POR_DEFECTO)
                .build()
        }
    }

    AndroidView(modifier = Modifier.fillMaxSize(), factory = { mapView })
}
