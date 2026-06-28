package ec.cnel.sgaie.movil.map

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import ec.cnel.sgaie.movil.data.ColaSincronizacionRepository
import ec.cnel.sgaie.movil.data.ConflictoSincronizacionRepository
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacionRepository
import ec.cnel.sgaie.movil.data.PosteRepository
import ec.cnel.sgaie.movil.data.SectorTrabajoRepository
import ec.cnel.sgaie.movil.data.TramoRedRepository
import ec.cnel.sgaie.movil.sync.ArcGisConfig
import ec.cnel.sgaie.movil.sync.ArcGisRestClient
import ec.cnel.sgaie.movil.sync.ArcGisTokenProvider
import ec.cnel.sgaie.movil.sync.SincronizacionPreferencias
import ec.cnel.sgaie.movil.sync.SincronizadorCambios
import ec.cnel.sgaie.movil.sync.SincronizacionWorker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Pantalla "Sincronizar cambios" (§5.3, M5): dispara manualmente
 * [SincronizadorCambios] contra el Feature Service indicado.
 *
 * `# TODO: igual que [DescargaSectorScreen], la captura manual de URL/token
 * es un placeholder hasta tener login OAuth2 real (§9/§13). M5 además
 * reutiliza esta misma URL/token para que [ec.cnel.sgaie.movil.sync.SincronizacionWorker]
 * (sincronización periódica en segundo plano) los reusa vía SharedPreferences.`
 */
@Composable
fun SincronizacionScreen(
    onIrAConflictosPendientes: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var urlServicio by remember { mutableStateOf(ArcGisConfig.FEATURE_SERVICE_URL_PLACEHOLDER) }
    var token by remember { mutableStateOf("") }
    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var resultado by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Sincronizar cambios")
        Text(text = "Sube a ArcGIS los cambios pendientes de poste/tramo_red/equipo y fotografías ya cargadas (§5.3).")

        OutlinedTextField(value = urlServicio, onValueChange = { urlServicio = it }, label = { Text("URL del Feature Service") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = token, onValueChange = { token = it }, label = { Text("Token ArcGIS") }, modifier = Modifier.fillMaxWidth())

        error?.let { Text(text = it) }
        resultado?.let { Text(text = it) }

        if (enProgreso) {
            CircularProgressIndicator()
        } else {
            Button(onClick = {
                if (urlServicio.isBlank() || token.isBlank()) {
                    error = "Completa la URL del servicio y el token."
                    return@Button
                }
                error = null
                resultado = null
                enProgreso = true
                SincronizacionPreferencias.guardar(context, urlServicio, token)
                SincronizacionWorker.programar(context)
                scope.launch {
                    try {
                        val resultadoSync = withContext(Dispatchers.IO) {
                            val tokenProvider = ArcGisTokenProvider { token }
                            val restClient = ArcGisRestClient(urlServicio, tokenProvider)
                            val sincronizador = SincronizadorCambios(
                                client = restClient,
                                cola = ColaSincronizacionRepository(context),
                                conflictos = ConflictoSincronizacionRepository(context),
                                sectores = SectorTrabajoRepository(context),
                                postes = PosteRepository(context),
                                tramos = TramoRedRepository(context),
                                equipos = EquipoTelecomunicacionRepository(context),
                            )
                            sincronizador.sincronizar()
                        }
                        resultado = "Enviados: ${resultadoSync.enviados}, errores: ${resultadoSync.errores}, " +
                            "conflictos nuevos: ${resultadoSync.conflictos}, omitidos (fuera de alcance): ${resultadoSync.omitidos}"
                    } catch (excepcion: Exception) {
                        error = "Falló la sincronización: ${excepcion.message}"
                    } finally {
                        enProgreso = false
                    }
                }
            }) {
                Text("Sincronizar ahora")
            }
        }

        OutlinedButton(onClick = onIrAConflictosPendientes) {
            Text("Ver conflictos pendientes")
        }
    }
}
