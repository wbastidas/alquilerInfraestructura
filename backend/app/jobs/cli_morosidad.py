"""Punto de entrada para invocar la detección de morosidad desde el
Programador de tareas de Windows (fallback de §3.3 si el backend no corre
24/7):

    python -m app.jobs.cli_morosidad
"""

from app.db.session import SesionLocal
from app.jobs.morosidad import marcar_facturas_vencidas


def main() -> None:
    db = SesionLocal()
    try:
        vencidas = marcar_facturas_vencidas(db)
        print(f"Facturas marcadas como VENCIDA: {len(vencidas)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
