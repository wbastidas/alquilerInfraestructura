"""Job de auto-generación anual de AlquilerAnual (§6.6, §7.2).

Cada 1 de enero, recorre las operadoras con contrato vigente y crea su
AlquilerAnual del nuevo año, clonando la estructura de PostePorZona del año
anterior con montos en cero y estado PENDIENTE. Es idempotente: si el año ya
fue generado para una operadora, no lo duplica. Deja rastro en LogAuditoria y
genera una Alerta de facturación pendiente.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.alquiler_anual import AlquilerAnual, PostePorZona
from app.models.alerta import Alerta
from app.models.contrato import Contrato
from app.models.enums import (
    AccionAuditoria,
    EstadoContrato,
    EstadoPago,
    SeveridadAlerta,
    TipoAlerta,
)
from app.models.log_auditoria import LogAuditoria


def generar_alquileres_anuales(db: Session, anio: int | None = None) -> list[AlquilerAnual]:
    """Genera (de forma idempotente) los AlquilerAnual del `anio` dado para toda
    operadora con contrato vigente. Devuelve los registros recién creados."""
    anio = anio or date.today().year

    contratos_vigentes = db.scalars(
        select(Contrato).where(Contrato.estado == EstadoContrato.VIGENTE)
    ).all()

    creados: list[AlquilerAnual] = []
    operadoras_procesadas: set[int] = set()

    for contrato in contratos_vigentes:
        cable_operadora_id = contrato.cable_operadora_id
        if cable_operadora_id in operadoras_procesadas:
            continue
        operadoras_procesadas.add(cable_operadora_id)

        ya_existe = db.scalar(
            select(AlquilerAnual.id).where(
                AlquilerAnual.cable_operadora_id == cable_operadora_id,
                AlquilerAnual.anio == anio,
            )
        )
        if ya_existe is not None:
            continue

        anterior = db.scalar(
            select(AlquilerAnual)
            .options(selectinload(AlquilerAnual.postes_por_zona))
            .where(
                AlquilerAnual.cable_operadora_id == cable_operadora_id,
                AlquilerAnual.anio == anio - 1,
            )
            .order_by(AlquilerAnual.id.desc())
        )

        nuevo = AlquilerAnual(
            cable_operadora_id=cable_operadora_id,
            contrato_id=contrato.id,
            unidad_negocio_id=contrato.unidad_negocio_id,
            anio=anio,
            postes_sig=0,
            postes_fisicos=0,
            monto_facturado=Decimal("0"),
            monto_recaudado=Decimal("0"),
            monto_pendiente_recaudar=Decimal("0"),
            estado_pago=EstadoPago.PENDIENTE,
        )
        if anterior is not None:
            nuevo.postes_por_zona = [
                PostePorZona(
                    provincia=zona.provincia,
                    canton=zona.canton,
                    parroquia=zona.parroquia,
                    tipo_zona=zona.tipo_zona,
                    cantidad_postes=zona.cantidad_postes,
                    cantidad_ductos_m=zona.cantidad_ductos_m,
                    canon_unitario=zona.canon_unitario,
                    subtotal=Decimal("0"),
                )
                for zona in anterior.postes_por_zona
            ]
        db.add(nuevo)
        db.flush()  # asigna nuevo.id antes de referenciarlo en Alerta/LogAuditoria

        db.add(
            Alerta(
                tipo=TipoAlerta.SIG_ANUAL_PENDIENTE,
                entidad_tipo="ALQUILER_ANUAL",
                entidad_id=nuevo.id,
                unidad_negocio_id=nuevo.unidad_negocio_id,
                mensaje=(
                    f"Facturación pendiente del nuevo período {anio} para la operadora "
                    f"#{cable_operadora_id}."
                ),
                severidad=SeveridadAlerta.ADVERTENCIA,
            )
        )
        db.add(
            LogAuditoria(
                usuario_id=None,
                accion=AccionAuditoria.CREAR,
                entidad_tipo="AlquilerAnual",
                entidad_id=nuevo.id,
                descripcion=(
                    f"Auto-generación anual {anio} (job programado) para la operadora "
                    f"#{cable_operadora_id}."
                ),
            )
        )
        creados.append(nuevo)

    db.commit()
    return creados
