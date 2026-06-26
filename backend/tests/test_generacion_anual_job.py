"""Pruebas del job de auto-generación anual (§6.6, §7.2): idempotencia, clonación
de la estructura de zonas y rastro en Alerta/LogAuditoria."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.generacion_anual import generar_alquileres_anuales
from app.models.alerta import Alerta
from app.models.alquiler_anual import AlquilerAnual, PostePorZona
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import (
    CoberturaGeografica,
    EstadoContrato,
    EstadoPago,
    TipoAlerta,
    TipoZona,
)
from app.models.log_auditoria import LogAuditoria


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
    estado: EstadoContrato = EstadoContrato.VIGENTE,
) -> Contrato:
    contrato = Contrato(
        cable_operadora_id=cable_operadora_id,
        unidad_negocio_id=unidad_negocio_id,
        numero_contrato=numero_contrato,
        tipo_cobertura=CoberturaGeografica.LOCAL,
        estado=estado,
    )
    db_session.add(contrato)
    db_session.commit()
    return contrato


def test_generar_crea_alquiler_para_operadora_con_contrato_vigente(
    db_session: Session, usuario_local
):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    contrato = _crear_contrato(
        db_session, operadora.id, usuario_local.unidad_negocio_id, "CONT-001"
    )

    creados = generar_alquileres_anuales(db_session, anio=2025)

    assert len(creados) == 1
    nuevo = creados[0]
    assert nuevo.anio == 2025
    assert nuevo.contrato_id == contrato.id
    assert nuevo.estado_pago == EstadoPago.PENDIENTE
    assert nuevo.monto_facturado == Decimal("0")


def test_generar_es_idempotente(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    _crear_contrato(db_session, operadora.id, usuario_local.unidad_negocio_id, "CONT-001")

    primera = generar_alquileres_anuales(db_session, anio=2025)
    segunda = generar_alquileres_anuales(db_session, anio=2025)

    assert len(primera) == 1
    assert len(segunda) == 0
    total = db_session.scalars(
        select(AlquilerAnual).where(
            AlquilerAnual.cable_operadora_id == operadora.id, AlquilerAnual.anio == 2025
        )
    ).all()
    assert len(total) == 1


def test_generar_omite_operadoras_sin_contrato_vigente(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    _crear_contrato(
        db_session,
        operadora.id,
        usuario_local.unidad_negocio_id,
        "CONT-001",
        estado=EstadoContrato.TERMINADO,
    )

    creados = generar_alquileres_anuales(db_session, anio=2025)

    assert creados == []


def test_generar_clona_estructura_de_postes_por_zona_del_anio_anterior(
    db_session: Session, usuario_local
):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    contrato = _crear_contrato(
        db_session, operadora.id, usuario_local.unidad_negocio_id, "CONT-001"
    )
    anterior = AlquilerAnual(
        cable_operadora_id=operadora.id,
        contrato_id=contrato.id,
        unidad_negocio_id=usuario_local.unidad_negocio_id,
        anio=2024,
        monto_facturado=Decimal("90.00"),
        monto_recaudado=Decimal("90.00"),
        monto_pendiente_recaudar=Decimal("0"),
        estado_pago=EstadoPago.COMPLETO,
        postes_por_zona=[
            PostePorZona(
                provincia="Guayas",
                canton="Guayaquil",
                tipo_zona=TipoZona.CAPITAL_PROVINCIAL,
                cantidad_postes=10,
                canon_unitario=Decimal("9.00"),
                subtotal=Decimal("90.00"),
            )
        ],
    )
    db_session.add(anterior)
    db_session.commit()

    creados = generar_alquileres_anuales(db_session, anio=2025)

    assert len(creados) == 1
    nuevo = creados[0]
    assert len(nuevo.postes_por_zona) == 1
    zona = nuevo.postes_por_zona[0]
    assert zona.canton == "Guayaquil"
    assert zona.cantidad_postes == 10
    assert zona.subtotal == Decimal("0")  # montos en cero hasta la nueva facturación


def test_generar_crea_alerta_y_log_auditoria(db_session: Session, usuario_local):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id, "REG-001")
    _crear_contrato(db_session, operadora.id, usuario_local.unidad_negocio_id, "CONT-001")

    creados = generar_alquileres_anuales(db_session, anio=2025)
    nuevo = creados[0]

    alerta = db_session.scalar(
        select(Alerta).where(
            Alerta.entidad_id == nuevo.id, Alerta.tipo == TipoAlerta.SIG_ANUAL_PENDIENTE
        )
    )
    assert alerta is not None

    log = db_session.scalar(
        select(LogAuditoria).where(
            LogAuditoria.entidad_tipo == "AlquilerAnual", LogAuditoria.entidad_id == nuevo.id
        )
    )
    assert log is not None
