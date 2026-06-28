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

private enum class Pantalla { MAPA, DESCARGA_SECTOR, EDICION_ENTIDAD, NOTA_INCUMPLIMIENTO, NOTA_ACEPTACION_RUTA, FOTOGRAFIA_CAPTURA, SINCRONIZACION, CONFLICTOS_PENDIENTES }

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Si ya hubo una sincronización manual previa (URL/token persistidos
        // en SincronizacionPreferencias), reanuda el respaldo periódico (§5.3);
        // si no, el worker se omite a sí mismo hasta que existan credenciales.
        SincronizacionWorker.programar(this)
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
    }
}
