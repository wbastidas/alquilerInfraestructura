"""Pruebas del job de detección de vencimientos (§6.14, §7.2): contratos,
pólizas y títulos habilitantes dentro de la ventana de anticipación, e
idempotencia (no duplica alertas en corridas subsecuentes)."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.vencimientos import detectar_vencimientos
from app.models.alerta import Alerta
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import CoberturaGeografica, EstadoContrato, TipoAlerta


def _crear_operadora(
    db_session: Session, unidad_negocio_id: int, numero_registro: str
) -> CableOperadora:
    operadora = CableOperadora(
        numero_registro=numero_registro,
        nombre_empresa="Telecom Demo S.A.",
        cobertura_geografica=CoberturaGeografica.LOCAL,
        tipo_contrato=CoberturaGeografica.LOCAL,
        unidad_negocio_id=unidad_negocio_id,
    )
    db_session.add(operadora)
    db_session.commit()
    return operadora


def _crear_contrato(
    db_session: Session,
    cable_operadora_id: int,
    unidad_negocio_id: int,
    numero_contrato: str,
    **campos,
) -> Contrato:
    contrato = Contrato(
        cable_operadora_id=cable_operadora_id,
        unidad_negocio_id=unidad_negocio_id,
        numero_contrato=numero_contrato,
        tipo_cobertura=CoberturaGeografica.LOCAL,
        estado=EstadoContrato.VIGENTE,
        **campos,
    )
    db_session.add(contrato)
    db_session.commit()
    return contrato


def test_genera_alerta_para_contrato_proximo_a_vencer(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    contrato = _crear_contrato(
        db_session,
        operadora.id,
        usuario_local.unidad_negocio_id,
        "CONT-001",
        fecha_fin=date.today() + timedelta(days=10),
    )

    creadas = detectar_vencimientos(db_session)

    assert len(creadas) == 1
    assert creadas[0].tipo == TipoAlerta.VENCIMIENTO_CONTRATO
    assert creadas[0].entidad_id == contrato.id


def test_no_genera_alerta_para_vencimiento_fuera_de_la_ventana(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    _crear_contrato(
        db_session,
        operadora.id,
        usuario_local.unidad_negocio_id,
        "CONT-001",
        fecha_fin=date.today() + timedelta(days=365),
    )

    creadas = detectar_vencimientos(db_session)

    assert creadas == []


def test_genera_alerta_para_poliza_proxima_a_vencer(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    contrato = _crear_contrato(
        db_session,
        operadora.id,
        usuario_local.unidad_negocio_id,
        "CONT-001",
        poliza_vigencia_fin=date.today() + timedelta(days=5),
    )

    creadas = detectar_vencimientos(db_session)

    assert len(creadas) == 1
    assert creadas[0].tipo == TipoAlerta.VENCIMIENTO_POLIZA
    assert creadas[0].entidad_id == contrato.id


def test_genera_alerta_para_titulo_habilitante_proximo_a_vencer(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    operadora.titulo_habilitante_vigencia = date.today() + timedelta(days=15)
    db_session.commit()

    creadas = detectar_vencimientos(db_session)

    assert len(creadas) == 1
    assert creadas[0].tipo == TipoAlerta.VENCIMIENTO_TITULO
    assert creadas[0].entidad_id == operadora.id


def test_deteccion_es_idempotente(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    _crear_contrato(
        db_session,
        operadora.id,
        usuario_local.unidad_negocio_id,
        "CONT-001",
        fecha_fin=date.today() + timedelta(days=10),
    )

    primera_corrida = detectar_vencimientos(db_session)
    segunda_corrida = detectar_vencimientos(db_session)

    assert len(primera_corrida) == 1
    assert segunda_corrida == []
    total_alertas = db_session.scalars(select(Alerta)).all()
    assert len(total_alertas) == 1
