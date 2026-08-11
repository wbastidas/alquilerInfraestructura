"""Pruebas del servicio de Alerta (§6.14): alcance por rol y marcado de leída."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermisoDenegado, RecursoNoEncontrado
from app.models.alerta import Alerta
from app.models.enums import SeveridadAlerta, TipoAlerta
from app.models.rol import Rol
from app.models.unidad_negocio import UnidadNegocio
from app.services import alerta as servicio

from tests.conftest import contexto_de


def _crear_alerta(
    db_session: Session, unidad_negocio_id, tipo=TipoAlerta.VENCIMIENTO_CONTRATO
) -> Alerta:
    alerta = Alerta(
        tipo=tipo,
        entidad_tipo="CONTRATO",
        entidad_id=1,
        unidad_negocio_id=unidad_negocio_id,
        mensaje="Vence en 10 días.",
        severidad=SeveridadAlerta.ADVERTENCIA,
    )
    db_session.add(alerta)
    db_session.commit()
    return alerta


def test_un_lista_solo_alertas_de_su_propia_un(
    db_session: Session,
    usuario_local,
    rol_un: Rol,
    unidad_negocio_a: UnidadNegocio,
    unidad_negocio_b: UnidadNegocio,
):
    _crear_alerta(db_session, unidad_negocio_a.id)
    _crear_alerta(db_session, unidad_negocio_b.id)
    usuario_un = contexto_de(usuario_local, rol_un)

    alertas = servicio.listar(db_session, usuario_un)

    assert len(alertas) == 1
    assert alertas[0].unidad_negocio_id == unidad_negocio_a.id


def test_matriz_lista_alertas_de_todas_las_un(
    db_session: Session,
    usuario_local,
    rol_matriz: Rol,
    unidad_negocio_a: UnidadNegocio,
    unidad_negocio_b: UnidadNegocio,
):
    _crear_alerta(db_session, unidad_negocio_a.id)
    _crear_alerta(db_session, unidad_negocio_b.id)
    usuario_matriz = contexto_de(usuario_local, rol_matriz)

    alertas = servicio.listar(db_session, usuario_matriz)

    assert len(alertas) == 2


def test_proveedor_no_puede_listar_alertas(
    db_session: Session, usuario_local, rol_proveedor: Rol, unidad_negocio_a: UnidadNegocio
):
    _crear_alerta(db_session, unidad_negocio_a.id)
    usuario_prov = contexto_de(usuario_local, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.listar(db_session, usuario_prov)


def test_un_marca_leida_su_propia_alerta(
    db_session: Session, usuario_local, rol_un: Rol, unidad_negocio_a: UnidadNegocio
):
    alerta = _crear_alerta(db_session, unidad_negocio_a.id)
    usuario_un = contexto_de(usuario_local, rol_un)

    actualizada = servicio.marcar_leida(db_session, alerta.id, usuario_un)

    assert actualizada.leida is True


def test_un_no_puede_marcar_leida_alerta_de_otra_un(
    db_session: Session,
    usuario_local,
    rol_un: Rol,
    unidad_negocio_b: UnidadNegocio,
):
    alerta = _crear_alerta(db_session, unidad_negocio_b.id)
    usuario_un = contexto_de(usuario_local, rol_un)

    with pytest.raises(PermisoDenegado):
        servicio.marcar_leida(db_session, alerta.id, usuario_un)


def test_marcar_leida_alerta_inexistente_falla(db_session: Session, usuario_local, rol_un: Rol):
    usuario_un = contexto_de(usuario_local, rol_un)

    with pytest.raises(RecursoNoEncontrado):
        servicio.marcar_leida(db_session, 99999, usuario_un)
