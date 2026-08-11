package ec.cnel.sgaie.movil

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import ec.cnel.sgaie.movil.map.ConflictosPendientesScreen
import ec.cnel.sgaie.movil.map.DescargaSectorScreen
import ec.cnel.sgaie.movil.map.EdicionEntidadScreen
import ec.cnel.sgaie.movil.map.FeatureSeleccionada
import ec.cnel.sgaie.movil.map.FotografiaCapturaScreen
import ec.cnel.sgaie.movil.map.NotaAceptacionRutaScreen
import ec.cnel.sgaie.movil.map.NotaIncumplimientoScreen
import ec.cnel.sgaie.movil.map.OfflineMapScreen
import ec.cnel.sgaie.movil.map.SincronizacionScreen
import ec.cnel.sgaie.movil.sync.SincronizacionWorker
import ec.cnel.sgaie.movil.ui.theme.SgaieTheme

private enum class Pantalla(val titulo: String) {
    MAPA("SGAIE Móvil"),
    DESCARGA_SECTOR("Descargar sector"),
    EDICION_ENTIDAD("Editar elemento"),
    NOTA_INCUMPLIMIENTO("Nota de incumplimiento"),
    NOTA_ACEPTACION_RUTA("Aceptación de ruta"),
    FOTOGRAFIA_CAPTURA("Fotografía"),
    SINCRONIZACION("Sincronización"),
    CONFLICTOS_PENDIENTES("Conflictos pendientes"),
}

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Si ya hubo una sincronización manual previa (URL/token persistidos
        // en SincronizacionPreferencias), reanuda el respaldo periódico (§5.3);
        // si no, el worker se omite a sí mismo hasta que existan credenciales.
        SincronizacionWorker.programar(this)
        setContent {
            SgaieTheme {
                SgaieApp()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SgaieApp() {
    var pantalla by remember { mutableStateOf(Pantalla.MAPA) }
    var disparadorActualizacionSector by remember { mutableIntStateOf(0) }
    var entidadSeleccionada by remember { mutableStateOf<FeatureSeleccionada?>(null) }
    var sectorParaNotaRuta by remember { mutableStateOf<Long?>(null) }

    // El botón atrás del sistema regresa al mapa desde cualquier pantalla,
    // en vez de salir de la aplicación.
    BackHandler(enabled = pantalla != Pantalla.MAPA) { pantalla = Pantalla.MAPA }

    Scaffold(
        topBar = {
            if (pantalla != Pantalla.MAPA) {
                TopAppBar(
                    title = { Text(text = pantalla.titulo) },
                    navigationIcon = {
                        IconButton(onClick = { pantalla = Pantalla.MAPA }) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Volver al mapa",
                            )
                        }
                    },
                )
            }
        },
    ) { relleno ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno),
        ) {
            when (pantalla) {
                Pantalla.MAPA -> OfflineMapScreen(
                    disparadorActualizacionSector = disparadorActualizacionSector,
                    onIrADescargarSector = { pantalla = Pantalla.DESCARGA_SECTOR },
                    onEntidadSeleccionada = { entidadTipo, entidadId ->
                        entidadSeleccionada = FeatureSeleccionada(entidadTipo, entidadId)
                        pantalla = Pantalla.EDICION_ENTIDAD
                    },
                    onRegistrarAceptacionRuta = { sectorTrabajoId ->
                        sectorParaNotaRuta = sectorTrabajoId
                        pantalla = Pantalla.NOTA_ACEPTACION_RUTA
                    },
                    onIrASincronizar = { pantalla = Pantalla.SINCRONIZACION },
                )

                Pantalla.DESCARGA_SECTOR -> DescargaSectorScreen(
                    onSectorDescargado = {
                        disparadorActualizacionSector++
                        pantalla = Pantalla.MAPA
                    },
                )

                Pantalla.EDICION_ENTIDAD -> entidadSeleccionada?.let { seleccion ->
                    EdicionEntidadScreen(
                        entidadTipo = seleccion.entidadTipo,
                        entidadId = seleccion.entidadId,
                        onGuardado = { pantalla = Pantalla.MAPA },
                        onEliminado = { pantalla = Pantalla.MAPA },
                        onRegistrarIncumplimiento = { entidadTipo, entidadId ->
                            entidadSeleccionada = FeatureSeleccionada(entidadTipo, entidadId)
                            pantalla = Pantalla.NOTA_INCUMPLIMIENTO
                        },
                        onTomarFotografia = { entidadTipo, entidadId ->
                            entidadSeleccionada = FeatureSeleccionada(entidadTipo, entidadId)
                            pantalla = Pantalla.FOTOGRAFIA_CAPTURA
                        },
                    )
                }

                Pantalla.NOTA_INCUMPLIMIENTO -> entidadSeleccionada?.let { seleccion ->
                    NotaIncumplimientoScreen(
                        entidadTipo = seleccion.entidadTipo,
                        entidadId = seleccion.entidadId,
                        onGuardado = { pantalla = Pantalla.MAPA },
                        onTomarFotografia = { entidadTipo, entidadId ->
                            entidadSeleccionada = FeatureSeleccionada(entidadTipo, entidadId)
                            pantalla = Pantalla.FOTOGRAFIA_CAPTURA
                        },
                    )
                }

                Pantalla.NOTA_ACEPTACION_RUTA -> sectorParaNotaRuta?.let { sectorTrabajoId ->
                    NotaAceptacionRutaScreen(
                        sectorTrabajoId = sectorTrabajoId,
                        onGuardado = { pantalla = Pantalla.MAPA },
                        onTomarFotografia = { entidadTipo, entidadId ->
                            entidadSeleccionada = FeatureSeleccionada(entidadTipo, entidadId)
                            pantalla = Pantalla.FOTOGRAFIA_CAPTURA
                        },
                    )
                }

                Pantalla.FOTOGRAFIA_CAPTURA -> entidadSeleccionada?.let { seleccion ->
                    FotografiaCapturaScreen(
                        entidadTipo = seleccion.entidadTipo,
                        entidadId = seleccion.entidadId,
                        onFinalizado = { pantalla = Pantalla.MAPA },
                    )
                }

                Pantalla.SINCRONIZACION -> SincronizacionScreen(
                    onIrAConflictosPendientes = { pantalla = Pantalla.CONFLICTOS_PENDIENTES },
                )

                Pantalla.CONFLICTOS_PENDIENTES -> ConflictosPendientesScreen()
            }
        }
    }
}
