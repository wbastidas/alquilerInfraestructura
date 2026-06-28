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
import ec.cnel.sgaie.movil.data.DecisionAceptacionRuta
import ec.cnel.sgaie.movil.data.NotaAceptacionRuta
import ec.cnel.sgaie.movil.data.NotaAceptacionRutaRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID

/**
 * Dominio §4.6: verificación en campo de una ruta propuesta del sector.
 *
 * `# TODO: el trazado verificado (geometria LINESTRING, §4.6) no se captura
 * aquí — falta dibujo interactivo sobre el mapa, misma limitación explícita
 * que la extensión geográfica en DescargaSectorScreen (M2).`
 */
@Composable
fun NotaAceptacionRutaScreen(sectorTrabajoId: Long, onGuardado: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { NotaAceptacionRutaRepository(context) }

    var rutaReferencia by remember { mutableStateOf("") }
    var decision by remember { mutableStateOf(DecisionAceptacionRuta.ACEPTADA.name) }
    var comentario by remember { mutableStateOf("") }
    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Registrar aceptación de ruta")

        OutlinedTextField(value = rutaReferencia, onValueChange = { rutaReferencia = it }, label = { Text("Referencia de ruta (opcional)") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(
            value = decision,
            onValueChange = { decision = it },
            label = { Text("Decisión (${DecisionAceptacionRuta.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(value = comentario, onValueChange = { comentario = it }, label = { Text("Comentario") }, modifier = Modifier.fillMaxWidth())

        error?.let { Text(text = it) }

        if (enProgreso) {
            CircularProgressIndicator()
        } else {
            Button(onClick = {
                val decisionEnum = runCatching { DecisionAceptacionRuta.valueOf(decision) }.getOrNull()
                if (comentario.isBlank() || decisionEnum == null) {
                    error = "Completa el comentario y una decisión válida."
                    return@Button
                }
                error = null
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) {
                        repository.insertar(
                            NotaAceptacionRuta(
                                globalId = UUID.randomUUID().toString(),
                                sectorTrabajoId = sectorTrabajoId,
                                rutaReferencia = rutaReferencia.ifBlank { null },
                                decision = decisionEnum,
                                comentario = comentario,
                            ),
                        )
                    }
                    enProgreso = false
                    onGuardado()
                }
            }) { Text("Guardar nota") }
        }
    }
}
