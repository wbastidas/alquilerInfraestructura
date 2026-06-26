"""Programación del job de auto-generación anual (§7.2) vía APScheduler.

Fallback documentado en §3.3: si el proceso del backend no corre 24/7 en el
servidor Windows, usar el Programador de tareas de Windows para invocar
`python -m app.jobs.cli_generacion_anual` el 1 de enero en lugar de depender
de este scheduler en proceso.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SesionLocal
from app.jobs.generacion_anual import generar_alquileres_anuales

ID_JOB_GENERACION_ANUAL = "generacion-anual-alquileres"


def _ejecutar_generacion_anual() -> None:
    db = SesionLocal()
    try:
        generar_alquileres_anuales(db)
    finally:
        db.close()


def crear_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="America/Guayaquil")
    scheduler.add_job(
        _ejecutar_generacion_anual,
        trigger="cron",
        month=1,
        day=1,
        hour=0,
        minute=5,
        id=ID_JOB_GENERACION_ANUAL,
        replace_existing=True,
    )
    return scheduler
