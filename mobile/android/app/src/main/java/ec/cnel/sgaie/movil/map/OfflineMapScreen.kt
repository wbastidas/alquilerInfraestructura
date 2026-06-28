package ec.cnel.sgaie.movil.map

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import ec.cnel.sgaie.movil.R
import ec.cnel.sgaie.movil.data.EntidadTipo
import ec.cnel.sgaie.movil.data.SectorTrabajoRepository
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.Style
import java.io.File

/** Centro de cámara por defecto: Guayaquil (placeholder hasta tener sectores reales). */
private val CENTRO_POR_DEFECTO = LatLng(-2.1709979, -79.9223592)
private const val ZOOM_POR_DEFECTO = 12.0
private const val NOMBRE_MBTILES_DEMO = "sector-demo.mbtiles"

@Composable
fun OfflineMapScreen(
    disparadorActualizacionSector: Int = 0,
    onIrADescargarSector: () -> Unit = {},
    onEntidadSeleccionada: (EntidadTipo, Long) -> Unit = { _, _ -> },
    onRegistrarAceptacionRuta: (Long) -> Unit = {},
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val mbtilesFile = remember {
        File(context.getExternalFilesDir("tiles"), NOMBRE_MBTILES_DEMO)
    }
    var tileServer by remember { mutableStateOf<OfflineTileServer?>(null) }
    var mapaCargado by remember { mutableStateOf<MapLibreMap?>(null) }
    var sectorActualId by remember { mutableStateOf<Long?>(null) }

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
            mapa.setStyle(Style.Builder().fromJson(estiloJson)) {
                mapa.cameraPosition = CameraPosition.Builder()
                    .target(CENTRO_POR_DEFECTO)
                    .zoom(ZOOM_POR_DEFECTO)
                    .build()
                mapaCargado = mapa

                // M2: hasta que exista un selector de sector (la pantalla de
                // descarga solo agrega sectores nuevos), se dibuja el primer
                // sector ya extraído al GeoPackage local, si lo hay.
                val sector = SectorTrabajoRepository(context).listarTodos().firstOrNull()
                if (sector != null) {
                    sectorActualId = sector.id
                    SectorLayersRenderer.agregarCapasDeSector(mapa, context, sector.id)
                }

                // M3 (§5.2): selección de poste/tramo/equipo por tap, para editar
                // o registrar una nota de incumplimiento sobre la entidad tocada.
                mapa.addOnMapClickListener { puntoTocado ->
                    val seleccion = FeatureSeleccionHandler.seleccionarEn(mapa, puntoTocado)
                    if (seleccion != null) {
                        onEntidadSeleccionada(seleccion.entidadTipo, seleccion.entidadId)
                        true
                    } else {
                        false
                    }
                }
            }
        }
    }

    // Tras volver de DescargaSectorScreen con un sector nuevo, redibuja las
    // capas sobre el estilo ya cargado (sin recrear el mapa ni el servidor de tiles).
    LaunchedEffect(disparadorActualizacionSector) {
        if (disparadorActualizacionSector == 0) return@LaunchedEffect
        val mapa = mapaCargado ?: return@LaunchedEffect
        val sector = SectorTrabajoRepository(context).listarTodos().firstOrNull() ?: return@LaunchedEffect
        sectorActualId = sector.id
        SectorLayersRenderer.agregarCapasDeSector(mapa, context, sector.id)
    }

    Box(modifier = Modifier.fillMaxSize()) {
        AndroidView(modifier = Modifier.fillMaxSize(), factory = { mapView })
        FloatingActionButton(
            onClick = onIrADescargarSector,
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(16.dp),
        ) {
            Text(text = "⤓")
        }
        sectorActualId?.let { sectorId ->
            FloatingActionButton(
                onClick = { onRegistrarAceptacionRuta(sectorId) },
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .padding(16.dp),
            ) {
                Text(text = "✓")
            }
        }
    }
}
