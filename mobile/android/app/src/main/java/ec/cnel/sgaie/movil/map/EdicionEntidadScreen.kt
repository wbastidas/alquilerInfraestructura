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
import ec.cnel.sgaie.movil.data.EquipoTelecomunicacionRepository
import ec.cnel.sgaie.movil.data.EstadoEquipo
import ec.cnel.sgaie.movil.data.EstadoFisicoPoste
import ec.cnel.sgaie.movil.data.EstadoTramoRed
import ec.cnel.sgaie.movil.data.PosteRepository
import ec.cnel.sgaie.movil.data.TipoEquipo
import ec.cnel.sgaie.movil.data.TipoPoste
import ec.cnel.sgaie.movil.data.TipoRed
import ec.cnel.sgaie.movil.data.TramoRedRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Edición offline de la entidad seleccionada en el mapa (M3, §5.2): muestra
 * los campos editables del poste/tramo/equipo tocado y permite guardar
 * (encola `EDITAR`), eliminar (encola `ELIMINAR`), o saltar a registrar una
 * nota de incumplimiento sobre esta misma entidad.
 */
@Composable
fun EdicionEntidadScreen(
    entidadTipo: EntidadTipo,
    entidadId: Long,
    onGuardado: () -> Unit,
    onEliminado: () -> Unit,
    onRegistrarIncumplimiento: (EntidadTipo, Long) -> Unit,
    onTomarFotografia: (EntidadTipo, Long) -> Unit,
) {
    when (entidadTipo) {
        EntidadTipo.POSTE -> EdicionPoste(
            posteId = entidadId,
            onGuardado = onGuardado,
            onEliminado = onEliminado,
            onRegistrarIncumplimiento = { onRegistrarIncumplimiento(EntidadTipo.POSTE, entidadId) },
            onTomarFotografia = { onTomarFotografia(EntidadTipo.POSTE, entidadId) },
        )
        EntidadTipo.TRAMO_RED -> EdicionTramo(
            tramoId = entidadId,
            onGuardado = onGuardado,
            onEliminado = onEliminado,
            onRegistrarIncumplimiento = { onRegistrarIncumplimiento(EntidadTipo.TRAMO_RED, entidadId) },
            onTomarFotografia = { onTomarFotografia(EntidadTipo.TRAMO_RED, entidadId) },
        )
        EntidadTipo.EQUIPO -> EdicionEquipo(
            equipoId = entidadId,
            onGuardado = onGuardado,
            onEliminado = onEliminado,
            onRegistrarIncumplimiento = { onRegistrarIncumplimiento(EntidadTipo.EQUIPO, entidadId) },
            onTomarFotografia = { onTomarFotografia(EntidadTipo.EQUIPO, entidadId) },
        )
        EntidadTipo.SECTOR -> Text(text = "El sector de trabajo no se edita desde aquí.")
    }
}

@Composable
private fun EdicionPoste(
    posteId: Long,
    onGuardado: () -> Unit,
    onEliminado: () -> Unit,
    onRegistrarIncumplimiento: () -> Unit,
    onTomarFotografia: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { PosteRepository(context) }
    val original = remember(posteId) { repository.obtenerPorId(posteId) }

    if (original == null) {
        Text(text = "No se encontró el poste.")
        return
    }

    var codigoPoste by remember { mutableStateOf(original.codigoPoste) }
    var tipoPoste by remember { mutableStateOf(original.tipoPoste.name) }
    var alturaM by remember { mutableStateOf(original.alturaM?.toString() ?: "") }
    var capacidadCables by remember { mutableStateOf(original.capacidadCables?.toString() ?: "") }
    var estadoFisico by remember { mutableStateOf(original.estadoFisico.name) }
    var observaciones by remember { mutableStateOf(original.observaciones ?: "") }
    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Editar poste")
        OutlinedTextField(value = codigoPoste, onValueChange = { codigoPoste = it }, label = { Text("Código de poste") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(
            value = tipoPoste,
            onValueChange = { tipoPoste = it },
            label = { Text("Tipo de poste (${TipoPoste.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(value = alturaM, onValueChange = { alturaM = it }, label = { Text("Altura (m)") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = capacidadCables, onValueChange = { capacidadCables = it }, label = { Text("Capacidad de cables") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(
            value = estadoFisico,
            onValueChange = { estadoFisico = it },
            label = { Text("Estado físico (${EstadoFisicoPoste.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(value = observaciones, onValueChange = { observaciones = it }, label = { Text("Observaciones") }, modifier = Modifier.fillMaxWidth())

        error?.let { Text(text = it) }

        if (enProgreso) {
            CircularProgressIndicator()
        } else {
            Button(onClick = {
                val tipoPosteEnum = runCatching { TipoPoste.valueOf(tipoPoste) }.getOrNull()
                val estadoFisicoEnum = runCatching { EstadoFisicoPoste.valueOf(estadoFisico) }.getOrNull()
                if (codigoPoste.isBlank() || tipoPosteEnum == null || estadoFisicoEnum == null) {
                    error = "Completa el código de poste y valores válidos de tipo y estado físico."
                    return@Button
                }
                val actualizado = original.copy(
                    codigoPoste = codigoPoste,
                    tipoPoste = tipoPosteEnum,
                    alturaM = alturaM.toDoubleOrNull(),
                    capacidadCables = capacidadCables.toIntOrNull(),
                    estadoFisico = estadoFisicoEnum,
                    observaciones = observaciones.ifBlank { null },
                )
                error = null
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) { repository.actualizar(actualizado) }
                    enProgreso = false
                    onGuardado()
                }
            }) { Text("Guardar") }

            OutlinedButton(onClick = {
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) { repository.eliminar(posteId) }
                    enProgreso = false
                    onEliminado()
                }
            }) { Text("Eliminar poste") }

            OutlinedButton(onClick = onRegistrarIncumplimiento) { Text("Registrar nota de incumplimiento") }
            OutlinedButton(onClick = onTomarFotografia) { Text("Tomar fotografía") }
        }
    }
}

@Composable
private fun EdicionTramo(
    tramoId: Long,
    onGuardado: () -> Unit,
    onEliminado: () -> Unit,
    onRegistrarIncumplimiento: () -> Unit,
    onTomarFotografia: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { TramoRedRepository(context) }
    val original = remember(tramoId) { repository.obtenerPorId(tramoId) }

    if (original == null) {
        Text(text = "No se encontró el tramo de red.")
        return
    }

    var tipoRed by remember { mutableStateOf(original.tipoRed.name) }
    var longitudM by remember { mutableStateOf(original.longitudM?.toString() ?: "") }
    var estado by remember { mutableStateOf(original.estado.name) }
    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Editar tramo de red")
        OutlinedTextField(
            value = tipoRed,
            onValueChange = { tipoRed = it },
            label = { Text("Tipo de red (${TipoRed.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(value = longitudM, onValueChange = { longitudM = it }, label = { Text("Longitud (m)") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(
            value = estado,
            onValueChange = { estado = it },
            label = { Text("Estado (${EstadoTramoRed.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )

        error?.let { Text(text = it) }

        if (enProgreso) {
            CircularProgressIndicator()
        } else {
            Button(onClick = {
                val tipoRedEnum = runCatching { TipoRed.valueOf(tipoRed) }.getOrNull()
                val estadoEnum = runCatching { EstadoTramoRed.valueOf(estado) }.getOrNull()
                if (tipoRedEnum == null || estadoEnum == null) {
                    error = "Tipo de red y estado deben ser valores válidos."
                    return@Button
                }
                val actualizado = original.copy(tipoRed = tipoRedEnum, longitudM = longitudM.toDoubleOrNull(), estado = estadoEnum)
                error = null
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) { repository.actualizar(actualizado) }
                    enProgreso = false
                    onGuardado()
                }
            }) { Text("Guardar") }

            OutlinedButton(onClick = {
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) { repository.eliminar(tramoId) }
                    enProgreso = false
                    onEliminado()
                }
            }) { Text("Eliminar tramo") }

            OutlinedButton(onClick = onRegistrarIncumplimiento) { Text("Registrar nota de incumplimiento") }
            OutlinedButton(onClick = onTomarFotografia) { Text("Tomar fotografía") }
        }
    }
}

@Composable
private fun EdicionEquipo(
    equipoId: Long,
    onGuardado: () -> Unit,
    onEliminado: () -> Unit,
    onRegistrarIncumplimiento: () -> Unit,
    onTomarFotografia: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { EquipoTelecomunicacionRepository(context) }
    val original = remember(equipoId) { repository.obtenerPorId(equipoId) }

    if (original == null) {
        Text(text = "No se encontró el equipo.")
        return
    }

    var marca by remember { mutableStateOf(original.marca ?: "") }
    var modelo by remember { mutableStateOf(original.modelo ?: "") }
    var numeroSerie by remember { mutableStateOf(original.numeroSerie ?: "") }
    var estado by remember { mutableStateOf(original.estado.name) }
    var enProgreso by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Editar equipo (${TipoEquipo.entries.joinToString(", ")})")
        OutlinedTextField(value = marca, onValueChange = { marca = it }, label = { Text("Marca") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = modelo, onValueChange = { modelo = it }, label = { Text("Modelo") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = numeroSerie, onValueChange = { numeroSerie = it }, label = { Text("Número de serie") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(
            value = estado,
            onValueChange = { estado = it },
            label = { Text("Estado (${EstadoEquipo.entries.joinToString(", ")})") },
            modifier = Modifier.fillMaxWidth(),
        )

        error?.let { Text(text = it) }

        if (enProgreso) {
            CircularProgressIndicator()
        } else {
            Button(onClick = {
                val estadoEnum = runCatching { EstadoEquipo.valueOf(estado) }.getOrNull()
                if (estadoEnum == null) {
                    error = "El estado debe ser un valor válido."
                    return@Button
                }
                val actualizado = original.copy(
                    marca = marca.ifBlank { null },
                    modelo = modelo.ifBlank { null },
                    numeroSerie = numeroSerie.ifBlank { null },
                    estado = estadoEnum,
                )
                error = null
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) { repository.actualizar(actualizado) }
                    enProgreso = false
                    onGuardado()
                }
            }) { Text("Guardar") }

            OutlinedButton(onClick = {
                enProgreso = true
                scope.launch {
                    withContext(Dispatchers.IO) { repository.eliminar(equipoId) }
                    enProgreso = false
                    onEliminado()
                }
            }) { Text("Eliminar equipo") }

            OutlinedButton(onClick = onRegistrarIncumplimiento) { Text("Registrar nota de incumplimiento") }
            OutlinedButton(onClick = onTomarFotografia) { Text("Tomar fotografía") }
        }
    }
}
