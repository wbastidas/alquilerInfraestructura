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
import ec.cnel.sgaie.movil.data.EntidadTipo
import ec.cnel.sgaie.movil.data.Gravedad
import ec.cnel.sgaie.movil.data.NotaIncumplimiento
import ec.cnel.sgaie.movil.data.NotaIncumplimientoRepository
import ec.cnel.sgaie.movil.data.TipoIncumplimiento
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID

/** Dominio §4.5: registro de campo de un incumplimiento sobre la entidad seleccionada, encolado para sync (§5.2). */
@Composable
fun NotaIncumplimientoScreen(
    entidadTipo: EntidadTipo,
    entidadId: Long,
    onGuardado: () -> Unit,
    onTomarFotografia: (EntidadTipo, Long) -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { NotaIncumplimientoRepository(context) }

    var tipoIncumplimiento by remember { mutableStateOf(TipoIncumplimiento.OTRO.name) }
    var descripcion by remember { mutableStateOf("") }
    var gravedad by remember { mutableStateOf(Gravedad.LEVE.name) }
    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var notaGuardada by remember { mutableStateOf(false) }

    if (notaGuardada) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(text = "Nota de incumplimiento guardada y encolada para sincronización.")
            Button(onClick = { onTomarFotografia(entidadTipo, entidadId) }) { Text("Tomar fotografía de evidencia") }
            OutlinedButton(onClick = onGuardado) { Text("Finalizar") }
        }
        return
    }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Registrar nota de incumplimiento")
        Text(text = "Entidad: $entidadTipo #$entidadId")

        OutlinedTextField(
            value = tipoIncumplimiento,
            onValueChange = { tipoIncumplimiento = it },
            label = { Text("Tipo (${TipoIncumplimiento.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(value = descripcion, onValueChange = { descripcion = it }, label = { Text("Descripción") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(
            value = gravedad,
            onValueChange = { gravedad = it },
            label = { Text("Gravedad (${Gravedad.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )

        error?.let { Text(text = it) }

        if (enProgreso) {
            CircularProgressIndicator()
        } else {
            Button(onClick = {
                val tipoIncumplimientoEnum = runCatching { TipoIncumplimiento.valueOf(tipoIncumplimiento) }.getOrNull()
                val gravedadEnum = runCatching { Gravedad.valueOf(gravedad) }.getOrNull()
                if (descripcion.isBlank() || tipoIncumplimientoEnum == null || gravedadEnum == null) {
                    error = "Completa la descripción y valores válidos de tipo y gravedad."
                    return@Button
                }
                error = null
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) {
                        repository.insertar(
                            NotaIncumplimiento(
                                globalId = UUID.randomUUID().toString(),
                                entidadTipo = entidadTipo,
                                entidadId = entidadId,
                                tipoIncumplimiento = tipoIncumplimientoEnum,
                                descripcion = descripcion,
                                gravedad = gravedadEnum,
                            ),
                        )
                    }
                    enProgreso = false
                    notaGuardada = true
                }
            }) { Text("Guardar nota") }
        }
    }
}
