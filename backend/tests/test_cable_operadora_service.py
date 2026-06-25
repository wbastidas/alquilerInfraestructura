"""Pruebas del servicio de CableOperadora (§6.4, §7.1): alcance por UN (§5.2)."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermisoDenegado, RecursoNoEncontrado
from app.models.enums import CoberturaGeografica
from app.models.unidad_negocio import UnidadNegocio
from app.schemas.cable_operadora import CableOperadoraCrear
from app.services import cable_operadora as servicio

from tests.conftest import contexto_de


def _datos_operadora(
    unidad_negocio_id: int, numero_registro: str = "REG-001"
) -> CableOperadoraCrear:
    return CableOperadoraCrear(
        numero_registro=numero_registro,
        nombre_empresa="Telecom Demo S.A.",
        cobertura_geografica=CoberturaGeografica.LOCAL,
        tipo_contrato=CoberturaGeografica.LOCAL,
        unidad_negocio_id=unidad_negocio_id,
    )


def test_un_puede_crear_operadora_en_su_propia_un(db_session: Session, usuario_local, rol_un):
    usuario = contexto_de(usuario_local, rol_un)
    operadora = servicio.crear(
        db_session, _datos_operadora(usuario_local.unidad_negocio_id), usuario
    )
    assert operadora.id is not None
    assert operadora.unidad_negocio_id == usuario_local.unidad_negocio_id


def test_un_no_puede_crear_operadora_en_otra_un(
    db_session: Session, usuario_local, rol_un, unidad_negocio_b: UnidadNegocio
):
    usuario = contexto_de(usuario_local, rol_un)
    with pytest.raises(PermisoDenegado):
        servicio.crear(db_session, _datos_operadora(unidad_negocio_b.id), usuario)


def test_un_solo_lista_operadoras_de_su_propia_un(
    db_session: Session, usuario_local, rol_un, rol_superadmin, unidad_negocio_b: UnidadNegocio
):
    usuario_un = contexto_de(usuario_local, rol_un)
    servicio.crear(
        db_session, _datos_operadora(usuario_local.unidad_negocio_id, "REG-A"), usuario_un
    )

    usuario_superadmin = contexto_de(usuario_local, rol_superadmin)
    servicio.crear(db_session, _datos_operadora(unidad_negocio_b.id, "REG-B"), usuario_superadmin)

    operadoras_un = servicio.listar(db_session, usuario_un)
    assert [o.numero_registro for o in operadoras_un] == ["REG-A"]


def test_matriz_lista_operadoras_de_todas_las_un(
    db_session: Session,
    usuario_local,
    rol_un,
    rol_matriz,
    rol_superadmin,
    unidad_negocio_b: UnidadNegocio,
):
    usuario_un = contexto_de(usuario_local, rol_un)
    servicio.crear(
        db_session, _datos_operadora(usuario_local.unidad_negocio_id, "REG-A"), usuario_un
    )

    usuario_superadmin = contexto_de(usuario_local, rol_superadmin)
    servicio.crear(db_session, _datos_operadora(unidad_negocio_b.id, "REG-B"), usuario_superadmin)

    usuario_matriz = contexto_de(usuario_local, rol_matriz)
    operadoras = servicio.listar(db_session, usuario_matriz)
    assert {o.numero_registro for o in operadoras} == {"REG-A", "REG-B"}


def test_un_no_puede_obtener_operadora_de_otra_un(
    db_session: Session, usuario_local, rol_un, rol_superadmin, unidad_negocio_b: UnidadNegocio
):
    usuario_superadmin = contexto_de(usuario_local, rol_superadmin)
    operadora_ajena = servicio.crear(
        db_session, _datos_operadora(unidad_negocio_b.id, "REG-AJENA"), usuario_superadmin
    )

    usuario_un = contexto_de(usuario_local, rol_un)
    with pytest.raises(PermisoDenegado):
        servicio.obtener(db_session, operadora_ajena.id, usuario_un)


def test_obtener_operadora_inexistente_lanza_recurso_no_encontrado(
    db_session: Session, usuario_local, rol_un
):
    usuario = contexto_de(usuario_local, rol_un)
    with pytest.raises(RecursoNoEncontrado):
        servicio.obtener(db_session, 9999, usuario)
