"""Pruebas de integración del endpoint /roles (§2.1, §6.3) vía TestClient."""

from sqlalchemy.orm import Session

from app.core.security import hashear_password
from app.models.enums import TipoCuenta
from app.models.usuario import Usuario


def _crear_usuario_local(db_session: Session, rol_id: int) -> Usuario:
    usuario = Usuario(
        username="admin",
        nombre_completo="Administrador",
        correo="admin@cnel.example.ec",
        tipo_cuenta=TipoCuenta.LOCAL,
        password_hash=hashear_password("Admin123!"),
        rol_id=rol_id,
        unidad_negocio_id=None,
        activo=True,
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


def _login(cliente_api) -> str:
    respuesta = cliente_api.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"}
    )
    return respuesta.json()["access_token"]


def test_listar_roles_requiere_autenticacion(cliente_api):
    respuesta = cliente_api.get("/api/v1/roles")
    assert respuesta.status_code in (401, 403)


def test_listar_roles_devuelve_catalogo(cliente_api, db_session: Session, rol_superadmin, rol_un):
    _crear_usuario_local(db_session, rol_superadmin.id)
    access_token = _login(cliente_api)

    respuesta = cliente_api.get(
        "/api/v1/roles", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert respuesta.status_code == 200
    codigos = {rol["codigo"] for rol in respuesta.json()}
    assert codigos == {"SUPERADMIN", "UN_OPERADOR"}


def test_cualquier_rol_autenticado_puede_listar(cliente_api, db_session: Session, rol_un):
    usuario = Usuario(
        username="un_user",
        nombre_completo="Usuario UN",
        correo="un_user@cnel.example.ec",
        tipo_cuenta=TipoCuenta.LOCAL,
        password_hash=hashear_password("Clave123!"),
        rol_id=rol_un.id,
        unidad_negocio_id=None,
        activo=True,
    )
    db_session.add(usuario)
    db_session.commit()

    login = cliente_api.post(
        "/api/v1/auth/login", json={"username": "un_user", "password": "Clave123!"}
    )
    access_token = login.json()["access_token"]

    respuesta = cliente_api.get(
        "/api/v1/roles", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert respuesta.status_code == 200
    assert any(rol["codigo"] == "UN_OPERADOR" for rol in respuesta.json())
