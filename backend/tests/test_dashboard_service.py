"""Pruebas del servicio de Dashboard consolidado (§7.2): agregados por UN vs.
vista global de Matriz, y bloqueo de acceso para el Proveedor."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermisoDenegado
from app.models.alerta import Alerta
from app.models.alquiler_anual import AlquilerAnual
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import (
    CoberturaGeografica,
    EstadoContrato,
    EstadoNovedad,
    EstadoPago,
    SeveridadAlerta,
    TipoAlerta,
    TipoNovedad,
)
from app.models.novedad import Novedad
from app.models.rol import Rol
from app.models.unidad_negocio import UnidadNegocio
from app.services import dashboard as servicio

from tests.conftest import contexto_de


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


def _construir_escenario(db_session: Session, unidad_negocio_id: int, sufijo: str) -> None:
    operadora = _crear_operadora(db_session, unidad_negocio_id, f"REG-{sufijo}")
    contrato = Contrato(
        cable_operadora_id=operadora.id,
        unidad_negocio_id=unidad_negocio_id,
        numero_contrato=f"CONT-{sufijo}",
        tipo_cobertura=CoberturaGeografica.LOCAL,
        estado=EstadoContrato.VIGENTE,
    )
    db_session.add(contrato)
    db_session.commit()

    alquiler = AlquilerAnual(
        cable_operadora_id=operadora.id,
        contrato_id=contrato.id,
        unidad_negocio_id=unidad_negocio_id,
        anio=date.today().year,
        monto_facturado=Decimal("1000"),
        monto_recaudado=Decimal("400"),
        monto_pendiente_recaudar=Decimal("600"),
        estado_pago=EstadoPago.PARCIAL,
    )
    db_session.add(alquiler)

    novedad = Novedad(
        cable_operadora_id=operadora.id,
        unidad_negocio_id=unidad_negocio_id,
        tipo=TipoNovedad.INSPECCION_PROGRAMADA,
        estado=EstadoNovedad.PROGRAMADA,
    )
    db_session.add(novedad)

    alerta = Alerta(
        tipo=TipoAlerta.VENCIMIENTO_CONTRATO,
        entidad_tipo="CONTRATO",
        entidad_id=contrato.id,
        unidad_negocio_id=unidad_negocio_id,
        mensaje="Vence pronto.",
        severidad=SeveridadAlerta.ADVERTENCIA,
    )
    db_session.add(alerta)
    db_session.commit()


def test_un_ve_solo_su_propio_consolidado(
    db_session: Session,
    usuario_local,
    rol_un: Rol,
    unidad_negocio_a: UnidadNegocio,
    unidad_negocio_b: UnidadNegocio,
):
    _construir_escenario(db_session, unidad_negocio_a.id, "A")
    _construir_escenario(db_session, unidad_negocio_b.id, "B")
    usuario_un = contexto_de(usuario_local, rol_un)

    consolidado = servicio.obtener_consolidado(db_session, usuario_un)

    assert consolidado.total_operadoras == 1
    assert consolidado.total_contratos_vigentes == 1
    assert consolidado.monto_facturado == Decimal("1000")
    assert consolidado.monto_recaudado == Decimal("400")
    assert consolidado.monto_pendiente_recaudar == Decimal("600")
    assert consolidado.novedades_abiertas == 1
    assert consolidado.alertas_no_leidas == 1


def test_matriz_ve_consolidado_global(
    db_session: Session,
    usuario_local,
    rol_matriz: Rol,
    unidad_negocio_a: UnidadNegocio,
    unidad_negocio_b: UnidadNegocio,
):
    _construir_escenario(db_session, unidad_negocio_a.id, "A")
    _construir_escenario(db_session, unidad_negocio_b.id, "B")
    usuario_matriz = contexto_de(usuario_local, rol_matriz)

    consolidado = servicio.obtener_consolidado(db_session, usuario_matriz)

    assert consolidado.total_operadoras == 2
    assert consolidado.total_contratos_vigentes == 2
    assert consolidado.monto_facturado == Decimal("2000")
    assert consolidado.novedades_abiertas == 2
    assert consolidado.alertas_no_leidas == 2


def test_proveedor_no_puede_ver_el_dashboard(
    db_session: Session, usuario_local, rol_proveedor: Rol, unidad_negocio_a: UnidadNegocio
):
    _construir_escenario(db_session, unidad_negocio_a.id, "A")
    usuario_prov = contexto_de(usuario_local, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.obtener_consolidado(db_session, usuario_prov)
