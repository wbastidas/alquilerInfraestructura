"""Job de detección de vencimientos próximos (§6.14, §7.2): contratos, pólizas
de garantía y títulos habilitantes que vencen dentro de la ventana de
anticipación configurada (`dias_anticipacion_alerta_vencimiento`).

Es idempotente: si ya existe una Alerta del mismo tipo para la misma entidad,
no se genera una segunda en corridas subsecuentes.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import obtener_configuracion
from app.models.alerta import Alerta
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import AccionAuditoria, EstadoContrato, SeveridadAlerta, TipoAlerta
from app.models.log_auditoria import LogAuditoria


def _ya_alertado(db: Session, tipo: TipoAlerta, entidad_id: int) -> bool:
    return (
        db.scalar(select(Alerta.id).where(Alerta.tipo == tipo, Alerta.entidad_id == entidad_id))
        is not None
    )


def _generar_alerta(
    db: Session,
    tipo: TipoAlerta,
    entidad_tipo: str,
    entidad_id: int,
    unidad_negocio_id: int | None,
    mensaje: str,
) -> Alerta:
    alerta = Alerta(
        tipo=tipo,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        unidad_negocio_id=unidad_negocio_id,
        mensaje=mensaje,
        severidad=SeveridadAlerta.ADVERTENCIA,
    )
    db.add(alerta)
    db.add(
        LogAuditoria(
            usuario_id=None,
            accion=AccionAuditoria.CREAR,
            entidad_tipo="Alerta",
            entidad_id=entidad_id,
            descripcion=f"Alerta de vencimiento ({tipo.value}) generada por job programado.",
        )
    )
    return alerta


def detectar_vencimientos(db: Session, fecha_calculo: date | None = None) -> list[Alerta]:
    """Recorre contratos vigentes y operadoras buscando fechas de vencimiento
    dentro de la ventana de anticipación configurada, generando una Alerta
    por cada vencimiento próximo aún no alertado. Devuelve las alertas creadas."""
    fecha_calculo = fecha_calculo or date.today()
    config = obtener_configuracion()
    limite = fecha_calculo + timedelta(days=config.dias_anticipacion_alerta_vencimiento)

    creadas: list[Alerta] = []

    contratos = db.scalars(select(Contrato).where(Contrato.estado == EstadoContrato.VIGENTE)).all()
    for contrato in contratos:
        if (
            contrato.fecha_fin is not None
            and fecha_calculo <= contrato.fecha_fin <= limite
            and not _ya_alertado(db, TipoAlerta.VENCIMIENTO_CONTRATO, contrato.id)
        ):
            creadas.append(
                _generar_alerta(
                    db,
                    TipoAlerta.VENCIMIENTO_CONTRATO,
                    "CONTRATO",
                    contrato.id,
                    contrato.unidad_negocio_id,
                    f"El contrato {contrato.numero_contrato} vence el {contrato.fecha_fin}.",
                )
            )

        if (
            contrato.poliza_vigencia_fin is not None
            and fecha_calculo <= contrato.poliza_vigencia_fin <= limite
            and not _ya_alertado(db, TipoAlerta.VENCIMIENTO_POLIZA, contrato.id)
        ):
            creadas.append(
                _generar_alerta(
                    db,
                    TipoAlerta.VENCIMIENTO_POLIZA,
                    "CONTRATO",
                    contrato.id,
                    contrato.unidad_negocio_id,
                    (
                        f"La póliza de garantía del contrato {contrato.numero_contrato} vence "
                        f"el {contrato.poliza_vigencia_fin}."
                    ),
                )
            )

    operadoras = db.scalars(select(CableOperadora)).all()
    for operadora in operadoras:
        if (
            operadora.titulo_habilitante_vigencia is not None
            and fecha_calculo <= operadora.titulo_habilitante_vigencia <= limite
            and not _ya_alertado(db, TipoAlerta.VENCIMIENTO_TITULO, operadora.id)
        ):
            creadas.append(
                _generar_alerta(
                    db,
                    TipoAlerta.VENCIMIENTO_TITULO,
                    "CABLE_OPERADORA",
                    operadora.id,
                    operadora.unidad_negocio_id,
                    (
                        f"El título habilitante de {operadora.nombre_empresa} vence el "
                        f"{operadora.titulo_habilitante_vigencia}."
                    ),
                )
            )

    db.commit()
    return creadas
