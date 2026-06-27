"""Pruebas del servicio de Factura y Pago (§6.11, §7.4): alcance por rol,
registro de pagos, conciliación bancaria, intereses por mora y morosidad."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    PermisoDenegado,
    RecursoDuplicado,
    RecursoNoEncontrado,
    TransicionInvalida,
)
from app.models.alquiler_anual import AlquilerAnual
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import (
    CoberturaGeografica,
    EstadoContrato,
    EstadoFactura,
    EstadoPago,
    MetodoPago,
    TipoPago,
)
from app.models.unidad_negocio import UnidadNegocio
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.schemas.pago import FacturaCrear, PagoCrear
from app.services import pago as servicio

from tests.conftest import contexto_de


def _crear_operadora(
    db_session: Session, unidad_negocio_id: int, numero_registro: str = "REG-100"
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
    numero_contrato: str = "CONT-001",
) -> Contrato:
    contrato = Contrato(
        cable_operadora_id=cable_operadora_id,
        unidad_negocio_id=unidad_negocio_id,
        numero_contrato=numero_contrato,
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


def _crear_usuario_proveedor(
    db_session: Session, rol_proveedor: Rol, cable_operadora_id: int, username: str = "proveedor1"
) -> Usuario:
    usuario = Usuario(
        username=username,
        nombre_completo="Representante Proveedor",
        correo="proveedor@example.com",
        tipo_cuenta="PROVEEDOR",
        password_hash=None,
        rol_id=rol_proveedor.id,
        unidad_negocio_id=None,
        cable_operadora_id=cable_operadora_id,
        activo=True,
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


def _datos_factura(
    cable_operadora_id: int,
    contrato_id: int,
    alquiler_anual_id: int,
    numero_factura: str = "FAC-001",
    fecha_vencimiento: date | None = None,
    monto: Decimal = Decimal("100.00"),
) -> FacturaCrear:
    return FacturaCrear(
        cable_operadora_id=cable_operadora_id,
        contrato_id=contrato_id,
        alquiler_anual_id=alquiler_anual_id,
        numero_factura=numero_factura,
        fecha_emision=date.today(),
        fecha_vencimiento=fecha_vencimiento or (date.today() + timedelta(days=30)),
        monto=monto,
        iva=Decimal("0"),
    )


@pytest.fixture()
def escenario(db_session: Session, unidad_negocio_a: UnidadNegocio, rol_un: Rol, usuario_local):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    contrato = _crear_contrato(db_session, operadora.id, unidad_negocio_a.id)
    alquiler = _crear_alquiler_anual(db_session, operadora.id, contrato.id, unidad_negocio_a.id)
    usuario_un = contexto_de(usuario_local, rol_un)
    return operadora, contrato, alquiler, usuario_un


def test_un_crea_factura(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario

    factura = servicio.crear_factura(
        db_session,
        _datos_factura(operadora.id, contrato.id, alquiler.id),
        usuario_un,
    )

    assert factura.estado == EstadoFactura.EMITIDA
    assert factura.total == Decimal("100.00")


def test_proveedor_no_puede_crear_factura(db_session: Session, escenario, rol_proveedor: Rol):
    operadora, contrato, alquiler, _ = escenario
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.crear_factura(
            db_session,
            _datos_factura(operadora.id, contrato.id, alquiler.id),
            usuario_prov,
        )


def test_crear_factura_numero_duplicado_falla(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )

    with pytest.raises(RecursoDuplicado):
        servicio.crear_factura(
            db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
        )


def test_crear_factura_operadora_no_coincide_con_contrato_falla(
    db_session: Session, escenario, unidad_negocio_a: UnidadNegocio
):
    operadora, contrato, alquiler, usuario_un = escenario
    otra_operadora = _crear_operadora(db_session, unidad_negocio_a.id, "REG-200")

    with pytest.raises(ValueError):
        servicio.crear_factura(
            db_session,
            _datos_factura(otra_operadora.id, contrato.id, alquiler.id),
            usuario_un,
        )


def test_crear_factura_alquiler_anual_inexistente_falla(db_session: Session, escenario):
    operadora, contrato, _, usuario_un = escenario

    with pytest.raises(RecursoNoEncontrado):
        servicio.crear_factura(
            db_session, _datos_factura(operadora.id, contrato.id, 99999), usuario_un
        )


def test_un_de_otra_un_no_puede_crear_factura(
    db_session: Session,
    escenario,
    unidad_negocio_b: UnidadNegocio,
    rol_un: Rol,
):
    operadora, contrato, alquiler, _ = escenario
    otro_usuario = Usuario(
        username="un_b_user",
        nombre_completo="Usuario UN-B",
        correo="un_b@cnel.example.ec",
        tipo_cuenta="LOCAL",
        password_hash=None,
        rol_id=rol_un.id,
        unidad_negocio_id=unidad_negocio_b.id,
        activo=True,
    )
    db_session.add(otro_usuario)
    db_session.commit()
    usuario_b = contexto_de(otro_usuario, rol_un)

    with pytest.raises(PermisoDenegado):
        servicio.crear_factura(
            db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_b
        )


def test_registrar_pago_parcial_deja_factura_parcial(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )

    pago = servicio.registrar_pago(
        db_session,
        PagoCrear(
            factura_id=factura.id,
            monto=Decimal("40.00"),
            tipo=TipoPago.PARCIAL,
            metodo=MetodoPago.TRANSFERENCIA,
            fecha_pago=date.today(),
        ),
        usuario_un,
    )

    factura_actualizada = servicio.obtener_factura(db_session, factura.id, usuario_un)
    assert pago.monto == Decimal("40.00")
    assert factura_actualizada.estado == EstadoFactura.PARCIAL


def test_registrar_pago_total_deja_factura_pagada(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )

    servicio.registrar_pago(
        db_session,
        PagoCrear(
            factura_id=factura.id,
            monto=Decimal("100.00"),
            tipo=TipoPago.TOTAL,
            metodo=MetodoPago.TRANSFERENCIA,
            fecha_pago=date.today(),
        ),
        usuario_un,
    )

    factura_actualizada = servicio.obtener_factura(db_session, factura.id, usuario_un)
    assert factura_actualizada.estado == EstadoFactura.PAGADA


def test_proveedor_no_puede_registrar_pago(db_session: Session, escenario, rol_proveedor: Rol):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.registrar_pago(
            db_session,
            PagoCrear(
                factura_id=factura.id,
                monto=Decimal("100.00"),
                tipo=TipoPago.TOTAL,
                metodo=MetodoPago.TRANSFERENCIA,
                fecha_pago=date.today(),
            ),
            usuario_prov,
        )


def test_no_se_puede_pagar_factura_anulada(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )
    factura.estado = EstadoFactura.ANULADA
    db_session.commit()

    with pytest.raises(TransicionInvalida):
        servicio.registrar_pago(
            db_session,
            PagoCrear(
                factura_id=factura.id,
                monto=Decimal("100.00"),
                tipo=TipoPago.TOTAL,
                metodo=MetodoPago.TRANSFERENCIA,
                fecha_pago=date.today(),
            ),
            usuario_un,
        )


def test_conciliar_pago(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )
    pago = servicio.registrar_pago(
        db_session,
        PagoCrear(
            factura_id=factura.id,
            monto=Decimal("100.00"),
            tipo=TipoPago.TOTAL,
            metodo=MetodoPago.TRANSFERENCIA,
            fecha_pago=date.today(),
        ),
        usuario_un,
    )

    conciliado = servicio.conciliar_pago(db_session, pago.id, usuario_un)

    assert conciliado.conciliado is True
    assert conciliado.fecha_conciliacion == date.today()


def test_conciliar_pago_dos_veces_falla(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )
    pago = servicio.registrar_pago(
        db_session,
        PagoCrear(
            factura_id=factura.id,
            monto=Decimal("100.00"),
            tipo=TipoPago.TOTAL,
            metodo=MetodoPago.TRANSFERENCIA,
            fecha_pago=date.today(),
        ),
        usuario_un,
    )
    servicio.conciliar_pago(db_session, pago.id, usuario_un)

    with pytest.raises(TransicionInvalida):
        servicio.conciliar_pago(db_session, pago.id, usuario_un)


def test_proveedor_no_puede_conciliar(db_session: Session, escenario, rol_proveedor: Rol):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )
    pago = servicio.registrar_pago(
        db_session,
        PagoCrear(
            factura_id=factura.id,
            monto=Decimal("100.00"),
            tipo=TipoPago.TOTAL,
            metodo=MetodoPago.TRANSFERENCIA,
            fecha_pago=date.today(),
        ),
        usuario_un,
    )
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.conciliar_pago(db_session, pago.id, usuario_prov)


def test_proveedor_puede_listar_solo_sus_facturas(
    db_session: Session, escenario, rol_proveedor: Rol, unidad_negocio_a: UnidadNegocio
):
    operadora, contrato, alquiler, usuario_un = escenario
    servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )
    otra_operadora = _crear_operadora(db_session, unidad_negocio_a.id, "REG-200")
    otro_contrato = _crear_contrato(db_session, otra_operadora.id, unidad_negocio_a.id, "CONT-002")
    otro_alquiler = _crear_alquiler_anual(
        db_session, otra_operadora.id, otro_contrato.id, unidad_negocio_a.id
    )
    servicio.crear_factura(
        db_session,
        _datos_factura(otra_operadora.id, otro_contrato.id, otro_alquiler.id, "FAC-002"),
        usuario_un,
    )

    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    facturas = servicio.listar_facturas(db_session, usuario_prov)
    assert len(facturas) == 1
    assert facturas[0].cable_operadora_id == operadora.id


def test_calcular_interes_mora_es_cero_si_no_vencida(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session, _datos_factura(operadora.id, contrato.id, alquiler.id), usuario_un
    )

    assert servicio.calcular_interes_mora(factura) == Decimal("0.00")


def test_calcular_interes_mora_con_saldo_vencido(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    factura = servicio.crear_factura(
        db_session,
        _datos_factura(
            operadora.id,
            contrato.id,
            alquiler.id,
            fecha_vencimiento=date.today() - timedelta(days=10),
        ),
        usuario_un,
    )

    interes = servicio.calcular_interes_mora(factura, date.today())
    esperado = (Decimal("100.00") * Decimal("0.1671") * Decimal(10) / Decimal("365")).quantize(
        Decimal("0.01")
    )
    assert interes == esperado


def test_reporte_morosidad_incluye_solo_vencidas_con_saldo(db_session: Session, escenario):
    operadora, contrato, alquiler, usuario_un = escenario
    servicio.crear_factura(
        db_session,
        _datos_factura(
            operadora.id,
            contrato.id,
            alquiler.id,
            fecha_vencimiento=date.today() - timedelta(days=5),
        ),
        usuario_un,
    )
    servicio.crear_factura(
        db_session,
        _datos_factura(operadora.id, contrato.id, alquiler.id, numero_factura="FAC-002"),
        usuario_un,
    )

    reporte = servicio.reporte_morosidad(db_session, usuario_un)

    assert len(reporte) == 1
    assert reporte[0].dias_mora == 5
