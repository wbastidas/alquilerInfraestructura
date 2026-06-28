plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "ec.cnel.sgaie.movil"
    compileSdk = 34

    defaultConfig {
        applicationId = "ec.cnel.sgaie.movil"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0-m1"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.09.02"))

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.6")

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    // Render del mapa offline (sin SDK comercial, sin dependencia de ArcGIS Runtime).
    // TODO: confirmar la última versión estable disponible en momento de build real
    // (no hay acceso a Maven Central para resolver versiones en este sandbox).
    implementation("org.maplibre.gl:android-sdk:11.5.2")

    // Servidor HTTP embebido que expone el .mbtiles del sector descargado como
    // tiles XYZ en 127.0.0.1, consumido por MapLibre como RasterSource http(s).
    implementation("org.nanohttpd:nanohttpd:2.3.1")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
