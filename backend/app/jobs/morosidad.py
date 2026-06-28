"""Job de detección de morosidad y alertas de vencimiento (§7.4, §6.14).

Recorre las facturas no terminales (no PAGADA ni ANULADA), recalcula su estado
con la misma lógica que usa `app.services.pago.registrar_pago` y, para toda
factura que pasa a VENCIDA en esta corrida, genera una `Alerta` tipo
MOROSIDAD. Es idempotente: una factura que ya está VENCIDA no genera una
alerta duplicada en corridas subsecuentes.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.alerta import Alerta
from app.models.enums import AccionAuditoria, EstadoFactura, SeveridadAlerta, TipoAlerta
from app.models.log_auditoria import LogAuditoria
from app.models.pago import Factura
from app.services.pago import _recalcular_estado_factura, _saldo_pendiente


def marcar_facturas_vencidas(db: Session, fecha_calculo: date | None = None) -> list[Factura]:
    """Recalcula el estado de las facturas pendientes y genera alertas de
    morosidad para las que recién pasan a VENCIDA. Devuelve esas facturas."""
    fecha_calculo = fecha_calculo or date.today()

    facturas_pendientes = db.scalars(
        select(Factura)
        .options(selectinload(Factura.pagos), selectinload(Factura.contrato))
        .where(Factura.estado.not_in([EstadoFactura.PAGADA, EstadoFactura.ANULADA]))
    ).all()

    recien_vencidas: list[Factura] = []

    for factura in facturas_pendientes:
        estado_anterior = factura.estado
        _recalcular_estado_factura(factura)
        if factura.estado == EstadoFactura.VENCIDA and estado_anterior != EstadoFactura.VENCIDA:
            recien_vencidas.append(factura)
            db.add(
                Alerta(
                    tipo=TipoAlerta.MOROSIDAD,
                    entidad_tipo="FACTURA",
                    entidad_id=factura.id,
                    unidad_negocio_id=factura.contrato.unidad_negocio_id,
                    mensaje=(
                        f"Factura {factura.numero_factura} vencida con saldo pendiente de "
                        f"{_saldo_pendiente(factura)} desde el {factura.fecha_vencimiento}."
                    ),
                    severidad=SeveridadAlerta.CRITICA,
                )
            )
            db.add(
                LogAuditoria(
                    usuario_id=None,
                    accion=AccionAuditoria.EDITAR,
                    entidad_tipo="Factura",
                    entidad_id=factura.id,
                    descripcion=(
                        f"Factura {factura.numero_factura} marcada VENCIDA por job programado "
                        f"de morosidad (corrida {fecha_calculo})."
                    ),
                )
            )

    db.commit()
    return recien_vencidas
