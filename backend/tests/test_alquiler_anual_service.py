"""Pruebas del servicio de AlquilerAnual (§6.6, §7.2): cálculo de canon y alcance por UN."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermisoDenegado, RecursoDuplicado
from app.models.cable_operadora import CableOperadora
from app.models.catalogo_canon import CatalogoCanon
from app.models.enums import CoberturaGeografica, EstadoPago, TipoZona
from app.models.unidad_negocio import UnidadNegocio
from app.schemas.alquiler_anual import (
    AlquilerAnualActualizar,
    AlquilerAnualCrear,
    PostePorZonaCrear,
)
from app.services import alquiler_anual as servicio

from tests.conftest import contexto_de


def _sembrar_canon(db_session: Session) -> None:
    valores = {
        TipoZona.CAPITAL_PROVINCIAL: Decimal("9.00"),
        TipoZona.CABECERA_CANTONAL: Decimal("7.02"),
        TipoZona.OTRO_SECTOR: Decimal("6.03"),
    }
    for tipo_zona, valor in valores.items():
        db_session.add(
            CatalogoCanon(
                tipo_zona=tipo_zona,
                valor=valor,
                vigente_desde=date(2016, 1, 1),
                referencia_normativa="Oficio MEER-SDCE-2016-0181-OF",
            )
        )
    db_session.commit()


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


def _datos_alquiler(
    cable_operadora_id: int, unidad_negocio_id: int, anio: int = 2025
) -> AlquilerAnualCrear:
    return AlquilerAnualCrear(
        cable_operadora_id=cable_operadora_id,
        unidad_negocio_id=unidad_negocio_id,
        anio=anio,
        postes_por_zona=[
            PostePorZonaCrear(
                provincia="Guayas",
                canton="Guayaquil",
                tipo_zona=TipoZona.CAPITAL_PROVINCIAL,
                cantidad_postes=10,
            ),
            PostePorZonaCrear(
                provincia="Guayas",
                canton="Durán",
                tipo_zona=TipoZona.CABECERA_CANTONAL,
                cantidad_postes=5,
            ),
        ],
    )


def test_crear_alquiler_anual_calcula_canon_por_zona(db_session: Session, usuario_local, rol_un):
    _sembrar_canon(db_session)
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    usuario = contexto_de(usuario_local, rol_un)

    alquiler = servicio.crear(
        db_session,
        _datos_alquiler(operadora.id, usuario_local.unidad_negocio_id),
        usuario,
    )

    assert alquiler.monto_facturado == Decimal("125.10")  # 10*9.00 + 5*7.02
    assert alquiler.monto_pendiente_recaudar == Decimal("125.10")
    assert alquiler.estado_pago == EstadoPago.PENDIENTE
    zonas = {z.canton: z.subtotal for z in alquiler.postes_por_zona}
    assert zonas["Guayaquil"] == Decimal("90.00")
    assert zonas["Durán"] == Decimal("35.10")


def test_un_no_puede_crear_alquiler_en_otra_un(
    db_session: Session, usuario_local, rol_un, unidad_negocio_b: UnidadNegocio
):
    _sembrar_canon(db_session)
    operadora = _crear_operadora(db_session, unidad_negocio_b.id)
    usuario = contexto_de(usuario_local, rol_un)

    with pytest.raises(PermisoDenegado):
        servicio.crear(db_session, _datos_alquiler(operadora.id, unidad_negocio_b.id), usuario)


def test_crear_alquiler_duplicado_para_misma_operadora_y_anio_lanza_error(
    db_session: Session, usuario_local, rol_un
):
    _sembrar_canon(db_session)
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    usuario = contexto_de(usuario_local, rol_un)
    datos = _datos_alquiler(operadora.id, usuario_local.unidad_negocio_id)
    servicio.crear(db_session, datos, usuario)

    with pytest.raises(RecursoDuplicado):
        servicio.crear(db_session, datos, usuario)


def test_actualizar_monto_recaudado_recalcula_estado_pago(
    db_session: Session, usuario_local, rol_un
):
    _sembrar_canon(db_session)
    operadora = _crear_operadora(db_session, usuario_local.unidad_negocio_id)
    usuario = contexto_de(usuario_local, rol_un)
    alquiler = servicio.crear(
        db_session, _datos_alquiler(operadora.id, usuario_local.unidad_negocio_id), usuario
    )

    parcial = servicio.actualizar(
        db_session,
        alquiler.id,
        AlquilerAnualActualizar(monto_recaudado=Decimal("50.00")),
        usuario,
    )
    assert parcial.estado_pago == EstadoPago.PARCIAL
    assert parcial.monto_pendiente_recaudar == Decimal("75.10")

    completo = servicio.actualizar(
        db_session,
        alquiler.id,
        AlquilerAnualActualizar(monto_recaudado=Decimal("125.10")),
        usuario,
    )
    assert completo.estado_pago == EstadoPago.COMPLETO
    assert completo.monto_pendiente_recaudar == Decimal("0.00")
