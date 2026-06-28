"""Servicio de Dashboard consolidado (§7.2, §10): vista resumen del estado
operativo, financiero y de alertas, con el mismo alcance por rol que el resto
del sistema (Matriz/Superadmin = consolidado global, UN = solo su propia UN).
El Proveedor no tiene acceso: es una herramienta de gestión interna de CNEL
EP, no parte de su expediente.

Las sumas y conteos se calculan en Python sobre colecciones ya filtradas por
SQLAlchemy en vez de `func.sum()`/`func.count()` de SQL, para mantener el
mismo comportamiento entre SQLite (pruebas) y MariaDB (producción) —
precedente de §6.6/§6.11 (`alquiler_anual.py`, `pago.py`).
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto
from app.core.exceptions import PermisoDenegado
from app.models.alerta import Alerta
from app.models.alquiler_anual import AlquilerAnual
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import EstadoContrato, EstadoFactura, EstadoNovedad, EstadoSolicitud
from app.models.novedad import Novedad
from app.models.pago import Factura
from app.models.solicitud import Solicitud
from app.schemas.dashboard import DashboardConsolidado
from app.services.base import aplicar_alcance_un

_ESTADOS_SOLICITUD_TERMINALES = {EstadoSolicitud.FINALIZADA, EstadoSolicitud.RECHAZADA}


def obtener_consolidado(
    db: Session, usuario_actual: UsuarioContexto, anio: int | None = None
) -> DashboardConsolidado:
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no tiene acceso al dashboard consolidado.")
    anio = anio or date.today().year

    operadoras = list(
        db.scalars(
            aplicar_alcance_un(
                select(CableOperadora), CableOperadora.unidad_negocio_id, usuario_actual
            )
        )
    )

    contratos = list(
        db.scalars(aplicar_alcance_un(select(Contrato), Contrato.unidad_negocio_id, usuario_actual))
    )
    contratos_vigentes = [c for c in contratos if c.estado == EstadoContrato.VIGENTE]

    alquileres_anio = list(
        db.scalars(
            aplicar_alcance_un(
                select(AlquilerAnual).where(AlquilerAnual.anio == anio),
                AlquilerAnual.unidad_negocio_id,
                usuario_actual,
            )
        )
    )
    monto_facturado = sum((a.monto_facturado for a in alquileres_anio), Decimal("0"))
    monto_recaudado = sum((a.monto_recaudado for a in alquileres_anio), Decimal("0"))
    monto_pendiente = sum((a.monto_pendiente_recaudar for a in alquileres_anio), Decimal("0"))

    solicitudes = list(
        db.scalars(
            aplicar_alcance_un(select(Solicitud), Solicitud.unidad_negocio_id, usuario_actual)
        )
    )
    solicitudes_pendientes = [
        s for s in solicitudes if s.estado not in _ESTADOS_SOLICITUD_TERMINALES
    ]

    novedades = list(
        db.scalars(aplicar_alcance_un(select(Novedad), Novedad.unidad_negocio_id, usuario_actual))
    )
    novedades_abiertas = [n for n in novedades if n.estado != EstadoNovedad.CERRADA]

    ids_alquiler_anio = {a.id for a in alquileres_anio}
    facturas_vencidas = 0
    if ids_alquiler_anio:
        facturas_vencidas = len(
            db.scalars(
                select(Factura).where(
                    Factura.alquiler_anual_id.in_(ids_alquiler_anio),
                    Factura.estado == EstadoFactura.VENCIDA,
                )
            ).all()
        )

    alertas_no_leidas = len(
        db.scalars(
            aplicar_alcance_un(
                select(Alerta).where(Alerta.leida.is_(False)),
                Alerta.unidad_negocio_id,
                usuario_actual,
            )
        ).all()
    )

    return DashboardConsolidado(
        anio=anio,
        total_operadoras=len(operadoras),
        total_contratos_vigentes=len(contratos_vigentes),
        monto_facturado=monto_facturado,
        monto_recaudado=monto_recaudado,
        monto_pendiente_recaudar=monto_pendiente,
        solicitudes_pendientes=len(solicitudes_pendientes),
        novedades_abiertas=len(novedades_abiertas),
        facturas_vencidas=facturas_vencidas,
        alertas_no_leidas=alertas_no_leidas,
    )
