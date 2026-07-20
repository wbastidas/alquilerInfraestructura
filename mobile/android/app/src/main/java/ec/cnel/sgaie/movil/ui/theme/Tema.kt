package ec.cnel.sgaie.movil.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/**
 * Tema visual del componente móvil, en lugar del esquema morado por defecto
 * de Material 3.
 *
 * `# NOTA: paleta aproximada a la identidad institucional de CNEL EP (azul
 * corporativo + verde de energía); reemplazar por los valores exactos del
 * manual de marca oficial cuando el cliente lo facilite (§13).`
 */
private val AzulInstitucional = Color(0xFF00529B)
private val AzulOscuro = Color(0xFF003A6F)
private val AzulClaro = Color(0xFF8FC3EF)
private val VerdeEnergia = Color(0xFF43A047)
private val VerdeClaro = Color(0xFFA5D6A7)
private val RojoError = Color(0xFFB3261E)

private val EsquemaClaro = lightColorScheme(
    primary = AzulInstitucional,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD3E4F7),
    onPrimaryContainer = AzulOscuro,
    secondary = VerdeEnergia,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFD8EFD9),
    onSecondaryContainer = Color(0xFF1B5E20),
    error = RojoError,
)

private val EsquemaOscuro = darkColorScheme(
    primary = AzulClaro,
    onPrimary = AzulOscuro,
    primaryContainer = Color(0xFF1D4A73),
    onPrimaryContainer = Color(0xFFD3E4F7),
    secondary = VerdeClaro,
    onSecondary = Color(0xFF1B5E20),
    secondaryContainer = Color(0xFF2E5A31),
    onSecondaryContainer = Color(0xFFD8EFD9),
)

@Composable
fun SgaieTheme(
    temaOscuro: Boolean = isSystemInDarkTheme(),
    contenido: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (temaOscuro) EsquemaOscuro else EsquemaClaro,
        content = contenido,
    )
}
