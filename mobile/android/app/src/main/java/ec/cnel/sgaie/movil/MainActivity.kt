package ec.cnel.sgaie.movil

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import ec.cnel.sgaie.movil.map.DescargaSectorScreen
import ec.cnel.sgaie.movil.map.EdicionEntidadScreen
import ec.cnel.sgaie.movil.map.FeatureSeleccionada
import ec.cnel.sgaie.movil.map.NotaAceptacionRutaScreen
import ec.cnel.sgaie.movil.map.NotaIncumplimientoScreen
import ec.cnel.sgaie.movil.map.OfflineMapScreen

private enum class Pantalla { MAPA, DESCARGA_SECTOR, EDICION_ENTIDAD, NOTA_INCUMPLIMIENTO, NOTA_ACEPTACION_RUTA }

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface {
                    var pantalla by remember { mutableStateOf(Pantalla.MAPA) }
                    var disparadorActualizacionSector by remember { mutableIntStateOf(0) }
                    var entidadSeleccionada by remember { mutableStateOf<FeatureSeleccionada?>(null) }
                    var sectorParaNotaRuta by remember { mutableStateOf<Long?>(null) }

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
                            )
                        }

                        Pantalla.NOTA_INCUMPLIMIENTO -> entidadSeleccionada?.let { seleccion ->
                            NotaIncumplimientoScreen(
                                entidadTipo = seleccion.entidadTipo,
                                entidadId = seleccion.entidadId,
                                onGuardado = { pantalla = Pantalla.MAPA },
                            )
                        }

                        Pantalla.NOTA_ACEPTACION_RUTA -> sectorParaNotaRuta?.let { sectorTrabajoId ->
                            NotaAceptacionRutaScreen(
                                sectorTrabajoId = sectorTrabajoId,
                                onGuardado = { pantalla = Pantalla.MAPA },
                            )
                        }
                    }
                }
            }
        }
    }
}
