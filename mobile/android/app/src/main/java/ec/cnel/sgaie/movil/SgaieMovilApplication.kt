package ec.cnel.sgaie.movil

import android.app.Application
import org.maplibre.android.MapLibre

class SgaieMovilApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        MapLibre.getInstance(this)
    }
}
