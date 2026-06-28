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
import ec.cnel.sgaie.movil.map.OfflineMapScreen

private enum class Pantalla { MAPA, DESCARGA_SECTOR }

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface {
                    var pantalla by remember { mutableStateOf(Pantalla.MAPA) }
                    var disparadorActualizacionSector by remember { mutableIntStateOf(0) }

                    when (pantalla) {
                        Pantalla.MAPA -> OfflineMapScreen(
                            disparadorActualizacionSector = disparadorActualizacionSector,
                            onIrADescargarSector = { pantalla = Pantalla.DESCARGA_SECTOR },
                        )

                        Pantalla.DESCARGA_SECTOR -> DescargaSectorScreen(
                            onSectorDescargado = {
                                disparadorActualizacionSector++
                                pantalla = Pantalla.MAPA
                            },
                        )
                    }
                }
            }
        }
    }
}
