"""Fixtures comunes de pruebas: BD SQLite en memoria + cliente HTTP de FastAPI."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registra todos los modelos en Base.metadata)
from app.auth.deps import UsuarioContexto
from app.core.security import hashear_password
from app.db.base import Base
from app.db.session import obtener_db
from app.main import app
from app.models.enums import TipoCuenta
from app.models.rol import Rol
from app.models.unidad_negocio import UnidadNegocio
from app.models.usuario import Usuario


@pytest.fixture()
def db_session():
    """Una BD SQLite en memoria nueva por test, compartida entre conexiones (StaticPool)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SesionPrueba = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    sesion = SesionPrueba()
    try:
        yield sesion
    finally:
        sesion.close()
        engine.dispose()


@pytest.fixture()
def unidad_negocio_a(db_session: Session) -> UnidadNegocio:
    un = UnidadNegocio(codigo="UN-A", nombre="CNEL Unidad A", provincia="Provincia A", activo=True)
    db_session.add(un)
    db_session.commit()
    return un


@pytest.fixture()
def unidad_negocio_b(db_session: Session) -> UnidadNegocio:
    un = UnidadNegocio(codigo="UN-B", nombre="CNEL Unidad B", provincia="Provincia B", activo=True)
    db_session.add(un)
    db_session.commit()
    return un


@pytest.fixture()
def rol_superadmin(db_session: Session) -> Rol:
    rol = Rol(codigo="SUPERADMIN", nombre="Super Administrador")
    db_session.add(rol)
    db_session.commit()
    return rol


@pytest.fixture()
def rol_matriz(db_session: Session) -> Rol:
    rol = Rol(codigo="MATRIZ_CONSULTA", nombre="Matriz (solo lectura)")
    db_session.add(rol)
    db_session.commit()
    return rol


@pytest.fixture()
def rol_un(db_session: Session) -> Rol:
    rol = Rol(codigo="UN_OPERADOR", nombre="Unidad de Negocio")
    db_session.add(rol)
    db_session.commit()
    return rol


@pytest.fixture()
def usuario_local(db_session: Session, rol_un: Rol, unidad_negocio_a: UnidadNegocio) -> Usuario:
    usuario = Usuario(
        username="un_a_user",
        nombre_completo="Usuario UN-A",
        correo="un_a@cnel.example.ec",
        tipo_cuenta=TipoCuenta.LOCAL,
        password_hash=hashear_password("Clave123!"),
        rol_id=rol_un.id,
        unidad_negocio_id=unidad_negocio_a.id,
        activo=True,
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


def contexto_de(usuario: Usuario, rol: Rol) -> UsuarioContexto:
    return UsuarioContexto(
        id=usuario.id,
        username=usuario.username,
        rol=rol.codigo,
        unidad_negocio_id=usuario.unidad_negocio_id,
        tipo_cuenta=usuario.tipo_cuenta.value,
    )


@pytest.fixture()
def cliente_api(db_session: Session):
    """TestClient con la dependencia de BD sustituida por la sesión de prueba."""

    def _obtener_db_prueba():
        yield db_session

    app.dependency_overrides[obtener_db] = _obtener_db_prueba
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
