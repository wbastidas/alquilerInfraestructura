package ec.cnel.sgaie.movil.sync

import kotlinx.coroutines.async
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * El candado que evita que la extracción de un sector (§5.1) y la subida de
 * cambios (§5.3) toquen el mismo GeoPackage a la vez dentro de un dispositivo.
 */
class SincronizacionLockTest {

    @After
    fun liberar() {
        if (SincronizacionLock.mutex.isLocked) SincronizacionLock.mutex.unlock()
    }

    @Test
    fun `el segundo intento de tomar el candado falla mientras el primero lo retiene`() {
        assertTrue(SincronizacionLock.mutex.tryLock())
        assertFalse("Dos operaciones no deben correr a la vez", SincronizacionLock.mutex.tryLock())
    }

    @Test
    fun `el candado vuelve a estar disponible tras liberarse`() {
        assertTrue(SincronizacionLock.mutex.tryLock())
        SincronizacionLock.mutex.unlock()
        assertTrue(SincronizacionLock.mutex.tryLock())
    }

    @Test
    fun `es el mismo candado para todos los llamadores`() {
        // Descarga y sincronización lo alcanzan por el mismo objeto compartido:
        // si fueran instancias distintas, la exclusión mutua no serviría de nada.
        val desdeDescarga: Mutex = SincronizacionLock.mutex
        val desdeSincronizacion: Mutex = SincronizacionLock.mutex
        assertTrue(desdeDescarga === desdeSincronizacion)
    }

    @Test
    fun `solo una corrutina entra a la seccion critica`() = runTest {
        val entradas = mutableListOf<String>()

        val primera = async {
            if (SincronizacionLock.mutex.tryLock()) {
                entradas += "extraccion"
                true
            } else {
                false
            }
        }
        primera.await()

        val segunda = async {
            if (SincronizacionLock.mutex.tryLock()) {
                entradas += "sincronizacion"
                true
            } else {
                false
            }
        }

        assertFalse(segunda.await())
        assertTrue(entradas == listOf("extraccion"))
    }
}
