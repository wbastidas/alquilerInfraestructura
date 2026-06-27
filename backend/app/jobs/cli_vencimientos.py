"""Punto de entrada para invocar la detección de vencimientos desde el
Programador de tareas de Windows (fallback de §3.3 si el backend no corre
24/7):

    python -m app.jobs.cli_vencimientos
"""

from app.db.session import SesionLocal
from app.jobs.vencimientos import detectar_vencimientos


def main() -> None:
    db = SesionLocal()
    try:
        alertas = detectar_vencimientos(db)
        print(f"Alertas de vencimiento generadas: {len(alertas)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
