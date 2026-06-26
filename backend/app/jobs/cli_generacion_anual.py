"""Punto de entrada para invocar la generación anual desde el Programador de
tareas de Windows (fallback de §3.3 si el backend no corre 24/7):

    python -m app.jobs.cli_generacion_anual
"""

from app.db.session import SesionLocal
from app.jobs.generacion_anual import generar_alquileres_anuales


def main() -> None:
    db = SesionLocal()
    try:
        creados = generar_alquileres_anuales(db)
        print(f"AlquilerAnual generados: {len(creados)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
