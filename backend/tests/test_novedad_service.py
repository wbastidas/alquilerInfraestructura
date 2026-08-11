"""Pruebas del servicio de Novedad (§6.13, §7.6): alcance por rol, transiciones
de estado y carga de fotografías geolocalizadas."""

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermisoDenegado, RecursoNoEncontrado, TransicionInvalida
from app.models.cable_operadora import CableOperadora
from app.models.enums import CoberturaGeografica, EstadoNovedad, TipoNovedad
from app.models.rol import Rol
from app.models.unidad_negocio import UnidadNegocio
from app.models.usuario import Usuario
from app.schemas.novedad import NovedadActualizar, NovedadCrear
from app.services import novedad as servicio

from tests.conftest import contexto_de


class _ArchivoFalso:
    def __init__(self, filename: str, content_type: str):
        self.filename = filename
        self.content_type = content_type


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


def _datos_novedad(
    cable_operadora_id: int,
    unidad_negocio_id: int,
    tipo: TipoNovedad = TipoNovedad.INSPECCION_PROGRAMADA,
) -> NovedadCrear:
    return NovedadCrear(
        cable_operadora_id=cable_operadora_id,
        unidad_negocio_id=unidad_negocio_id,
        tipo=tipo,
        descripcion="Inspección de rutina del tramo norte.",
    )


@pytest.fixture()
def escenario(db_session: Session, unidad_negocio_a: UnidadNegocio, rol_un: Rol, usuario_local):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    usuario_un = contexto_de(usuario_local, rol_un)
    return operadora, usuario_un


def test_un_crea_novedad(db_session: Session, escenario, unidad_negocio_a: UnidadNegocio):
    operadora, usuario_un = escenario

    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )

    assert novedad.estado == EstadoNovedad.PROGRAMADA
    assert novedad.tipo == TipoNovedad.INSPECCION_PROGRAMADA


def test_proveedor_no_puede_crear_novedad(
    db_session: Session, escenario, rol_proveedor: Rol, unidad_negocio_a: UnidadNegocio
):
    operadora, _ = escenario
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.crear(db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_prov)


def test_un_de_otra_un_no_puede_crear_novedad(
    db_session: Session,
    escenario,
    unidad_negocio_a: UnidadNegocio,
    unidad_negocio_b: UnidadNegocio,
    rol_un: Rol,
):
    operadora, _ = escenario
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
        servicio.crear(db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_b)


def test_operadora_de_otra_un_no_puede_usarse_en_novedad(
    db_session: Session, escenario, unidad_negocio_a: UnidadNegocio, unidad_negocio_b: UnidadNegocio
):
    """La operadora indicada debe pertenecer a la UN indicada (consistencia entre §6.13 y §6.5)."""
    _, usuario_un = escenario
    operadora_otra_un = _crear_operadora(db_session, unidad_negocio_b.id, numero_registro="REG-200")

    with pytest.raises(ValueError):
        servicio.crear(
            db_session, _datos_novedad(operadora_otra_un.id, unidad_negocio_a.id), usuario_un
        )


def test_proveedor_puede_listar_solo_sus_novedades(
    db_session: Session, escenario, rol_proveedor: Rol, unidad_negocio_a: UnidadNegocio
):
    operadora, usuario_un = escenario
    servicio.crear(db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un)
    otra_operadora = _crear_operadora(db_session, unidad_negocio_a.id, "REG-200")
    servicio.crear(db_session, _datos_novedad(otra_operadora.id, unidad_negocio_a.id), usuario_un)

    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    novedades = servicio.listar(db_session, usuario_prov)
    assert len(novedades) == 1
    assert novedades[0].cable_operadora_id == operadora.id


def test_proveedor_no_puede_actualizar_novedad(
    db_session: Session, escenario, rol_proveedor: Rol, unidad_negocio_a: UnidadNegocio
):
    operadora, usuario_un = escenario
    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.actualizar(
            db_session,
            novedad.id,
            NovedadActualizar(estado=EstadoNovedad.EN_PROCESO),
            usuario_prov,
        )


def test_transicion_de_estado_valida(
    db_session: Session, escenario, unidad_negocio_a: UnidadNegocio
):
    operadora, usuario_un = escenario
    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )

    actualizada = servicio.actualizar(
        db_session, novedad.id, NovedadActualizar(estado=EstadoNovedad.EN_PROCESO), usuario_un
    )

    assert actualizada.estado == EstadoNovedad.EN_PROCESO


def test_transicion_de_estado_invalida_falla(
    db_session: Session, escenario, unidad_negocio_a: UnidadNegocio
):
    operadora, usuario_un = escenario
    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )

    with pytest.raises(TransicionInvalida):
        servicio.actualizar(
            db_session, novedad.id, NovedadActualizar(estado=EstadoNovedad.CERRADA), usuario_un
        )


def test_no_se_puede_transicionar_desde_estado_cerrado(
    db_session: Session, escenario, unidad_negocio_a: UnidadNegocio
):
    operadora, usuario_un = escenario
    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )
    for estado in (EstadoNovedad.EN_PROCESO, EstadoNovedad.EJECUTADA, EstadoNovedad.CERRADA):
        novedad = servicio.actualizar(
            db_session, novedad.id, NovedadActualizar(estado=estado), usuario_un
        )

    with pytest.raises(TransicionInvalida):
        servicio.actualizar(
            db_session,
            novedad.id,
            NovedadActualizar(estado=EstadoNovedad.EN_PROCESO),
            usuario_un,
        )


def test_actualizar_novedad_inexistente_falla(db_session: Session, escenario):
    _, usuario_un = escenario

    with pytest.raises(RecursoNoEncontrado):
        servicio.actualizar(
            db_session, 99999, NovedadActualizar(estado=EstadoNovedad.EN_PROCESO), usuario_un
        )


def test_subir_fotografia_de_novedad(
    db_session: Session, escenario, unidad_negocio_a: UnidadNegocio, directorio_documentos: Path
):
    operadora, usuario_un = escenario
    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )

    fotografia = servicio.subir_fotografia(
        db_session,
        novedad.id,
        _ArchivoFalso("poste.jpg", "image/jpeg"),
        b"contenido-jpg",
        usuario_un,
        latitud=Decimal("-2.1700000"),
        longitud=Decimal("-79.9200000"),
    )

    assert fotografia.novedad_id == novedad.id
    assert fotografia.latitud == Decimal("-2.1700000")
    novedad_actualizada = servicio.obtener(db_session, novedad.id, usuario_un)
    assert len(novedad_actualizada.fotografias) == 1


def test_proveedor_no_puede_subir_fotografia(
    db_session: Session,
    escenario,
    rol_proveedor: Rol,
    unidad_negocio_a: UnidadNegocio,
    directorio_documentos: Path,
):
    operadora, usuario_un = escenario
    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.subir_fotografia(
            db_session,
            novedad.id,
            _ArchivoFalso("poste.jpg", "image/jpeg"),
            b"contenido-jpg",
            usuario_prov,
        )


def test_subir_fotografia_extension_no_permitida_falla(
    db_session: Session, escenario, unidad_negocio_a: UnidadNegocio, directorio_documentos: Path
):
    operadora, usuario_un = escenario
    novedad = servicio.crear(
        db_session, _datos_novedad(operadora.id, unidad_negocio_a.id), usuario_un
    )

    with pytest.raises(ValueError):
        servicio.subir_fotografia(
            db_session,
            novedad.id,
            _ArchivoFalso("virus.exe", "application/octet-stream"),
            b"contenido",
            usuario_un,
        )
