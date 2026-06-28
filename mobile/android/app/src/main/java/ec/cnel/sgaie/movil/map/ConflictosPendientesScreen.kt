package ec.cnel.sgaie.movil.map

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import ec.cnel.sgaie.movil.data.ConflictoSincronizacion
import ec.cnel.sgaie.movil.data.ConflictoSincronizacionRepository

/**
 * Pantalla "Conflictos pendientes" (§5.4, M5): lista los conflictos que el
 * sincronizador no resolvió automáticamente (siempre `ELIMINADO_EN_SERVIDOR`,
 * o un `ERROR_NO_RECUPERABLE` persistente), mostrando ambas versiones del
 * registro para que el coordinador en campo decida.
 *
 * `# NOTA: la resolución en sí (p. ej. "descartar cambio local" / "forzar
 * reenvío") queda fuera de alcance de M5 (ver README/limitaciones); aquí
 * solo se permite "Descartar" la entrada de la lista una vez resuelta
 * manualmente fuera de la app, vía [ConflictoSincronizacionRepository.eliminar].`
 */
@Composable
fun ConflictosPendientesScreen() {
    val context = LocalContext.current
    val repositorio = remember { ConflictoSincronizacionRepository(context) }
    var conflictos by remember { mutableStateOf(repositorio.listarTodos()) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Conflictos pendientes")
        Text(text = "Cambios locales que ArcGIS no pudo aplicar automáticamente (§5.4).")

        if (conflictos.isEmpty()) {
            Text(text = "No hay conflictos pendientes.")
        }

        conflictos.forEach { conflicto ->
            TarjetaConflicto(
                conflicto = conflicto,
                onDescartar = {
                    repositorio.eliminar(conflicto.id)
                    conflictos = repositorio.listarTodos()
                },
            )
        }
    }
}

@Composable
private fun TarjetaConflicto(
    conflicto: ConflictoSincronizacion,
    onDescartar: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(text = "${conflicto.tablaOrigen} #${conflicto.entidadId} — ${conflicto.tipo}")
            Text(text = conflicto.mensaje)
            Text(text = "Versión local: ${conflicto.payloadLocalJson}")
            Text(text = "Versión servidor: ${conflicto.payloadServidorJson ?: "(no disponible)"}")
            Text(text = "Detectado: ${conflicto.creadoEn}")
            Button(onClick = onDescartar) {
                Text("Descartar")
            }
        }
    }
}
