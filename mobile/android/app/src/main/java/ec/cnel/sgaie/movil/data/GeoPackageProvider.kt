package ec.cnel.sgaie.movil.data

import android.content.Context
import mil.nga.geopackage.GeoPackage
import mil.nga.geopackage.GeoPackageFactory
import mil.nga.geopackage.features.columns.GeometryColumns
import mil.nga.geopackage.features.user.FeatureColumn
import mil.nga.geopackage.features.user.FeatureTableMetadata
import mil.nga.geopackage.geom.GeoPackageGeometryData
import mil.nga.geopackage.srs.SpatialReferenceSystem
import mil.nga.proj.ProjectionConstants
import mil.nga.proj.ProjectionFactory
import mil.nga.sf.GeometryType

/**
 * Punto único de acceso al GeoPackage local (mobile/ESPECIFICACION_MOVIL_OFFLINE.md
 * §3.2/§4): un único archivo .gpkg por instalación, con una tabla por cada
 * entidad de red (sector_trabajo, poste, tramo_red, equipo_telecomunicacion).
 *
 * Se usa la API de bajo nivel de la librería NGA GeoPackage Android (creación
 * manual de FeatureTable + GeometryColumns) en vez de un ORM, porque el
 * estándar OGC exige registrar la tabla en gpkg_contents/gpkg_geometry_columns
 * para que el archivo sea abrible con QGIS/ArcGIS Pro (requisito explícito
 * del documento de diseño, no una preferencia estética).
 *
 * Firmas verificadas contra geopackage-android 6.7.5 / geopackage-core 6.6.7
 * (FeatureTableMetadata.create + SpatialReferenceSystemDao.getOrCreate).
 */
object GeoPackageProvider {

    private const val SRS_WGS84 = ProjectionConstants.EPSG_WORLD_GEODETIC_SYSTEM

    @Volatile
    private var geoPackage: GeoPackage? = null

    fun obtener(context: Context): GeoPackage {
        return geoPackage ?: synchronized(this) {
            geoPackage ?: abrirOCrear(context).also { geoPackage = it }
        }
    }

    private fun abrirOCrear(context: Context): GeoPackage {
        val manager = GeoPackageFactory.getManager(context)
        val nombre = GeoPackageContract.NOMBRE_ARCHIVO_DEFAULT
        if (!manager.exists(nombre)) {
            manager.create(nombre)
        }
        return manager.open(nombre)
    }

    /**
     * Crea la tabla de feature `nombreTabla` si todavía no existe, con sus
     * columnas no-geométricas y una sola columna de geometría.
     *
     * [geometriaOpcional] queda solo documental: `FeatureTableMetadata` crea
     * la columna de geometría siempre nullable, lo cual cubre ambos casos
     * (las tablas sin geometría real —cola/conflictos/notas— simplemente
     * dejan la columna en NULL).
     */
    @Suppress("UNUSED_PARAMETER")
    fun crearTablaSiNoExiste(
        geoPackage: GeoPackage,
        nombreTabla: String,
        tipoGeometria: GeometryType,
        columnasAdicionales: List<FeatureColumn>,
        geometriaOpcional: Boolean = false,
    ) {
        if (geoPackage.isFeatureTable(nombreTabla)) return

        // getProjection recibe long; la constante EPSG es int en Java.
        val proyeccion = ProjectionFactory.getProjection(SRS_WGS84.toLong())
        val srs: SpatialReferenceSystem = geoPackage.spatialReferenceSystemDao.getOrCreate(proyeccion)

        val geometryColumns = GeometryColumns()
        geometryColumns.tableName = nombreTabla
        geometryColumns.columnName = COL_GEOMETRIA
        geometryColumns.geometryType = tipoGeometria
        geometryColumns.z = 0
        geometryColumns.m = 0
        geometryColumns.srs = srs

        // FeatureTableMetadata genera por sí misma la columna id (PK) y la de
        // geometría a partir de geometryColumns; solo se pasan las adicionales.
        geoPackage.createFeatureTable(
            FeatureTableMetadata.create(geometryColumns, GeoPackageContract.COL_ID, columnasAdicionales),
        )
    }

    const val COL_GEOMETRIA = "geometria"

    fun geometriaPuntoWgs84(longitud: Double, latitud: Double): GeoPackageGeometryData {
        val punto = mil.nga.sf.Point(longitud, latitud)
        return GeoPackageGeometryData(punto)
    }
}
