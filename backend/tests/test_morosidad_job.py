"""Pruebas del job de detección de morosidad (§7.4, §6.14): transición a VENCIDA
e idempotencia de la alerta generada."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.morosidad import marcar_facturas_vencidas
from app.models.alerta import Alerta
from app.models.alquiler_anual import AlquilerAnual
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import (
    CoberturaGeografica,
    EstadoContrato,
    EstadoFactura,
    EstadoPago,
    TipoAlerta,
)
from app.models.pago import Factura


def _crear_operadora(db_session: Session, unidad_negocio_id: int) -> CableOperadora:
    operadora = CableOperadora(
        numero_registro="REG-001",
        nombre_empresa="Telecom Demo S.A.",
        cobertura_geografica=CoberturaGeografica.LOCAL,
        tipo_contrato=CoberturaGeografica.LOCAL,
        unidad_negocio_id=unidad_negocio_id,
    )
    db_session.add(operadora)
    db_session.commit()
    return operadora


def _crear_contrato(
    db_session: Session, cable_operadora_id: int, unidad_negocio_id: int
) -> Contrato:
    contrato = Contrato(
        cable_operadora_id=cable_operadora_id,
        unidad_negocio_id=unidad_negocio_id,
        numero_contrato="CONT-001",
        tipo_cobertura=CoberturaGeografica.LOCAL,
        estado=EstadoContrato.VIGENTE,
    )
    db_session.add(contrato)
    db_session.commit()
    return contrato


def _crear_alquiler_anual(
    db_session: Session, cable_operadora_id: int, contrato_id: int, unidad_negocio_id: int
) -> AlquilerAnual:
    alquiler = AlquilerAnual(
        cable_operadora_id=cable_operadora_id,
        contrato_id=contrato_id,
        unidad_negocio_id=unidad_negocio_id,
        anio=2025,
        estado_pago=EstadoPago.PENDIENTE,
    )
    db_session.add(alquiler)
    db_session.commit()
    return alquiler


def _crear_factura(
    db_session: Session,
    cable_operadora_id: int,
    contrato_id: int,
    alquiler_anual_id: int,
    fecha_vencimiento: date,
    numero_factura: str = "FAC-001",
) -> Factura:
    factura = Factura(
        cable_operadora_id=cable_operadora_id,
        contrato_id=contrato_id,
        alquiler_anual_id=alquiler_anual_id,
        numero_factura=numero_factura,
        fecha_emision=date.today(),
        fecha_vencimiento=fecha_vencimiento,
        monto=Decimal("100.00"),
        iva=Decimal("0"),
        total=Decimal("100.00"),
        estado=EstadoFactura.EMITIDA,
    )
    db_session.add(factura)
    db_session.commit()
    return factura


def test_marca_factura_vencida_y_genera_alerta(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    contrato = _crear_contrato(db_session, operadora.id, usuario_local.unidad_negocio_id)
    alquiler = _crear_alquiler_anual(
        db_session, operadora.id, contrato.id, usuario_local.unidad_negocio_id
    )
    factura = _crear_factura(
        db_session,
        operadora.id,
        contrato.id,
        alquiler.id,
        fecha_vencimiento=date.today() - timedelta(days=3),
    )

    vencidas = marcar_facturas_vencidas(db_session)

    assert len(vencidas) == 1
    assert vencidas[0].id == factura.id
    db_session.refresh(factura)
    assert factura.estado == EstadoFactura.VENCIDA

    alerta = db_session.scalar(
        select(Alerta).where(Alerta.entidad_id == factura.id, Alerta.tipo == TipoAlerta.MOROSIDAD)
    )
    assert alerta is not None


def test_no_genera_alerta_duplicada_en_corridas_subsecuentes(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    contrato = _crear_contrato(db_session, operadora.id, usuario_local.unidad_negocio_id)
    alquiler = _crear_alquiler_anual(
        db_session, operadora.id, contrato.id, usuario_local.unidad_negocio_id
    )
    _crear_factura(
        db_session,
        operadora.id,
        contrato.id,
        alquiler.id,
        fecha_vencimiento=date.today() - timedelta(days=3),
    )

    primera = marcar_facturas_vencidas(db_session)
    segunda = marcar_facturas_vencidas(db_session)

    assert len(primera) == 1
    assert len(segunda) == 0


def test_no_marca_facturas_no_vencidas(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    contrato = _crear_contrato(db_session, operadora.id, usuario_local.unidad_negocio_id)
    alquiler = _crear_alquiler_anual(
        db_session, operadora.id, contrato.id, usuario_local.unidad_negocio_id
    )
    factura = _crear_factura(
        db_session,
        operadora.id,
        contrato.id,
        alquiler.id,
        fecha_vencimiento=date.today() + timedelta(days=10),
    )

    vencidas = marcar_facturas_vencidas(db_session)

    assert vencidas == []
    db_session.refresh(factura)
    assert factura.estado == EstadoFactura.EMITIDA
