"""Pruebas del servicio de Contrato (§6.5, §7.1): transiciones de estado y alcance por UN."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermisoDenegado, TransicionInvalida
from app.models.cable_operadora import CableOperadora
from app.models.enums import CoberturaGeografica, EstadoContrato
from app.models.unidad_negocio import UnidadNegocio
from app.schemas.contrato import ContratoActualizar, ContratoCrear
from app.services import contrato as servicio

from tests.conftest import contexto_de


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


def _datos_contrato(cable_operadora_id: int, unidad_negocio_id: int) -> ContratoCrear:
    return ContratoCrear(
        cable_operadora_id=cable_operadora_id,
        unidad_negocio_id=unidad_negocio_id,
        numero_contrato="CONT-001",
        tipo_cobertura=CoberturaGeografica.LOCAL,
    )


def test_contrato_se_crea_en_estado_en_juridico(db_session: Session, usuario_local, rol_un):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    usuario = contexto_de(usuario_local, rol_un)
    contrato = servicio.crear(
        db_session, _datos_contrato(operadora.id, usuario_local.unidad_negocio_id), usuario
    )
    assert contrato.estado == EstadoContrato.EN_JURIDICO


def test_un_no_puede_crear_contrato_en_otra_un(
    db_session: Session, usuario_local, rol_un, unidad_negocio_b: UnidadNegocio
):
    operadora = _crear_operadora(db_session, unidad_negocio_b.id)
    usuario = contexto_de(usuario_local, rol_un)
    with pytest.raises(PermisoDenegado):
        servicio.crear(db_session, _datos_contrato(operadora.id, unidad_negocio_b.id), usuario)


@pytest.mark.parametrize(
    ("estado_inicial", "estado_destino"),
    [
        (EstadoContrato.EN_JURIDICO, EstadoContrato.VIGENTE),
        (EstadoContrato.VIGENTE, EstadoContrato.EN_RENOVACION),
        (EstadoContrato.VIGENTE, EstadoContrato.SUSPENDIDO),
        (EstadoContrato.SUSPENDIDO, EstadoContrato.VIGENTE),
        (EstadoContrato.EN_RENOVACION, EstadoContrato.TERMINADO),
    ],
)
def test_transiciones_de_estado_permitidas(
    db_session: Session, usuario_local, rol_un, estado_inicial, estado_destino
):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    usuario = contexto_de(usuario_local, rol_un)
    contrato = servicio.crear(
        db_session, _datos_contrato(operadora.id, usuario_local.unidad_negocio_id), usuario
    )
    contrato.estado = estado_inicial
    db_session.commit()

    actualizado = servicio.actualizar(
        db_session, contrato.id, ContratoActualizar(estado=estado_destino), usuario
    )
    assert actualizado.estado == estado_destino


@pytest.mark.parametrize(
    ("estado_inicial", "estado_destino"),
    [
        (EstadoContrato.EN_JURIDICO, EstadoContrato.TERMINADO),
        (EstadoContrato.TERMINADO, EstadoContrato.VIGENTE),
        (EstadoContrato.SUSPENDIDO, EstadoContrato.TERMINADO),
    ],
)
def test_transiciones_de_estado_invalidas_son_rechazadas(
    db_session: Session, usuario_local, rol_un, estado_inicial, estado_destino
):
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    usuario = contexto_de(usuario_local, rol_un)
    contrato = servicio.crear(
        db_session, _datos_contrato(operadora.id, usuario_local.unidad_negocio_id), usuario
    )
    contrato.estado = estado_inicial
    db_session.commit()

    with pytest.raises(TransicionInvalida):
        servicio.actualizar(
            db_session, contrato.id, ContratoActualizar(estado=estado_destino), usuario
        )
