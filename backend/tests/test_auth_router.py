"""Pruebas de integración del endpoint /auth (§5.1, §10) vía TestClient (capa HTTP completa)."""

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


def test_login_exitoso_devuelve_tokens(cliente_api, db_session: Session, rol_superadmin):
    _crear_usuario_local(db_session, rol_superadmin.id)
    respuesta = cliente_api.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"}
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert "access_token" in cuerpo
    assert "refresh_token" in cuerpo


def test_login_con_credenciales_invalidas_devuelve_401(
    cliente_api, db_session: Session, rol_superadmin
):
    _crear_usuario_local(db_session, rol_superadmin.id)
    respuesta = cliente_api.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "ClaveIncorrecta"}
    )
    assert respuesta.status_code == 401


def test_ruta_protegida_sin_token_devuelve_401(cliente_api):
    respuesta = cliente_api.get("/api/v1/operadoras")
    assert respuesta.status_code in (401, 403)


def test_login_y_acceso_a_ruta_protegida_con_token(
    cliente_api, db_session: Session, rol_superadmin
):
    _crear_usuario_local(db_session, rol_superadmin.id)
    login = cliente_api.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "Admin123!"}
    )
    access_token = login.json()["access_token"]

    respuesta = cliente_api.get(
        "/api/v1/operadoras", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == []
