"""Programación de jobs en background (§7.2, §7.4) vía APScheduler.

Fallback documentado en §3.3: si el proceso del backend no corre 24/7 en el
servidor Windows, usar el Programador de tareas de Windows para invocar
`python -m app.jobs.cli_generacion_anual` (1 de enero),
`python -m app.jobs.cli_morosidad` (diario) y
`python -m app.jobs.cli_vencimientos` (diario) en lugar de depender de este
scheduler en proceso.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SesionLocal
from app.jobs.generacion_anual import generar_alquileres_anuales
from app.jobs.morosidad import marcar_facturas_vencidas
from app.jobs.vencimientos import detectar_vencimientos

ID_JOB_GENERACION_ANUAL = "generacion-anual-alquileres"
ID_JOB_MOROSIDAD = "deteccion-morosidad-facturas"
ID_JOB_VENCIMIENTOS = "deteccion-vencimientos-proximos"


def _ejecutar_generacion_anual() -> None:
    db = SesionLocal()
    try:
        generar_alquileres_anuales(db)
    finally:
        db.close()


def _ejecutar_deteccion_morosidad() -> None:
    db = SesionLocal()
    try:
        marcar_facturas_vencidas(db)
    finally:
        db.close()


def _ejecutar_deteccion_vencimientos() -> None:
    db = SesionLocal()
    try:
        detectar_vencimientos(db)
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
    scheduler.add_job(
        _ejecutar_deteccion_morosidad,
        trigger="cron",
        hour=1,
        minute=0,
        id=ID_JOB_MOROSIDAD,
        replace_existing=True,
    )
    scheduler.add_job(
        _ejecutar_deteccion_vencimientos,
        trigger="cron",
        hour=2,
        minute=0,
        id=ID_JOB_VENCIMIENTOS,
        replace_existing=True,
    )
    return scheduler
