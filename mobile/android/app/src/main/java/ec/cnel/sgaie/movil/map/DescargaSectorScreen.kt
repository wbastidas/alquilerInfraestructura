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
import ec.cnel.sgaie.movil.data.SectorTrabajo
import ec.cnel.sgaie.movil.sync.ArcGisConfig
import ec.cnel.sgaie.movil.sync.ArcGisRestClient
import ec.cnel.sgaie.movil.sync.ArcGisSectorExtractor
import ec.cnel.sgaie.movil.sync.ArcGisTokenProvider
import ec.cnel.sgaie.movil.sync.Envelope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import mil.nga.sf.LineString
import mil.nga.sf.Point
import mil.nga.sf.Polygon
import java.io.File
import java.util.UUID

/**
 * Pantalla "Descargar sector de trabajo" (§5.1, fin de M2): captura los datos
 * mínimos para invocar `createReplica` y dispara la extracción completa
 * orquestada por [ArcGisSectorExtractor].
 *
 * `# TODO: reemplazar la captura manual de URL/token/extensión por: (1) login
 * OAuth2 real contra el portal ArcGIS de CNEL EP (§9, pendiente de
 * confirmación), y (2) dibujo de la extensión geográfica sobre el propio
 * mapa en vez de campos numéricos (§5.1), una vez resuelto §13.`
 */
@Composable
fun DescargaSectorScreen(onSectorDescargado: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var urlServicio by remember { mutableStateOf(ArcGisConfig.FEATURE_SERVICE_URL_PLACEHOLDER) }
    var token by remember { mutableStateOf("") }
    var codigoSector by remember { mutableStateOf("") }
    var nombreSector by remember { mutableStateOf("") }
    var unidadNegocioId by remember { mutableStateOf("") }
    var usuarioResponsable by remember { mutableStateOf("") }
    var xmin by remember { mutableStateOf("") }
    var ymin by remember { mutableStateOf("") }
    var xmax by remember { mutableStateOf("") }
    var ymax by remember { mutableStateOf("") }

    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Descargar sector de trabajo")

        OutlinedTextField(value = urlServicio, onValueChange = { urlServicio = it }, label = { Text("URL del Feature Service") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = token, onValueChange = { token = it }, label = { Text("Token ArcGIS") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = codigoSector, onValueChange = { codigoSector = it }, label = { Text("Código de sector") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = nombreSector, onValueChange = { nombreSector = it }, label = { Text("Nombre de sector") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = unidadNegocioId, onValueChange = { unidadNegocioId = it }, label = { Text("Unidad de negocio (id)") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = usuarioResponsable, onValueChange = { usuarioResponsable = it }, label = { Text("Usuario responsable") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = xmin, onValueChange = { xmin = it }, label = { Text("Longitud mínima (xmin)") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = ymin, onValueChange = { ymin = it }, label = { Text("Latitud mínima (ymin)") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = xmax, onValueChange = { xmax = it }, label = { Text("Longitud máxima (xmax)") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = ymax, onValueChange = { ymax = it }, label = { Text("Latitud máxima (ymax)") }, modifier = Modifier.fillMaxWidth())

        error?.let { Text(text = it) }

        if (enProgreso) {
            CircularProgressIndicator()
        } else {
            Button(onClick = {
                val envelope = construirEnvelope(xmin, ymin, xmax, ymax)
                val unidadNegocioIdNumerica = unidadNegocioId.toIntOrNull()
                if (envelope == null || unidadNegocioIdNumerica == null ||
                    codigoSector.isBlank() || nombreSector.isBlank() || usuarioResponsable.isBlank() || token.isBlank()
                ) {
                    error = "Completa todos los campos; xmin/ymin/xmax/ymax y la unidad de negocio deben ser numéricos."
                    return@Button
                }

                error = null
                enProgreso = true
                scope.launch {
                    try {
                        withContext(Dispatchers.IO) {
                            val tokenProvider = ArcGisTokenProvider { token }
                            val restClient = ArcGisRestClient(urlServicio, tokenProvider)
                            val extractor = ArcGisSectorExtractor(context, restClient)
                            val sector = SectorTrabajo(
                                globalId = UUID.randomUUID().toString(),
                                codigo = codigoSector,
                                nombre = nombreSector,
                                geometria = poligonoDeEnvelope(envelope),
                                unidadNegocioId = unidadNegocioIdNumerica,
                                usuarioResponsable = usuarioResponsable,
                            )
                            val archivoTemporal = File(context.cacheDir, "replica-$codigoSector.geodatabase")
                            extractor.extraer(sector, envelope, archivoTemporal)
                        }
                        onSectorDescargado()
                    } catch (excepcion: Exception) {
                        error = "Falló la descarga del sector: ${excepcion.message}"
                    } finally {
                        enProgreso = false
                    }
                }
            }) {
                Text("Descargar")
            }
        }
    }
}

private fun construirEnvelope(xmin: String, ymin: String, xmax: String, ymax: String): Envelope? {
    val xminN = xmin.toDoubleOrNull() ?: return null
    val yminN = ymin.toDoubleOrNull() ?: return null
    val xmaxN = xmax.toDoubleOrNull() ?: return null
    val ymaxN = ymax.toDoubleOrNull() ?: return null
    return Envelope(xmin = xminN, ymin = yminN, xmax = xmaxN, ymax = ymaxN)
}

private fun poligonoDeEnvelope(envelope: Envelope): Polygon {
    val anillo = LineString(
        mutableListOf(
            Point(envelope.xmin, envelope.ymin),
            Point(envelope.xmax, envelope.ymin),
            Point(envelope.xmax, envelope.ymax),
            Point(envelope.xmin, envelope.ymax),
            Point(envelope.xmin, envelope.ymin),
        ),
    )
    return Polygon(mutableListOf(anillo))
}
