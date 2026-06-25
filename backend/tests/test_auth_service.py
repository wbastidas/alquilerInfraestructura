"""Pruebas del servicio de autenticación (§5.1, §4.1): login local, refresh y revocación."""

import pytest
from sqlalchemy.orm import Session

from app.auth import service as auth_service
from app.core.exceptions import CredencialesInvalidas, TokenInvalido, UsuarioInactivo
from app.core.security import hashear_password
from app.models.enums import TipoCuenta
from app.models.token_refresco import TokenRefrescoRevocado
from app.models.usuario import Usuario


def _crear_usuario_local(db_session: Session, rol_id: int, *, activo: bool = True) -> Usuario:
    usuario = Usuario(
        username="proveedor1",
        nombre_completo="Proveedor Demo",
        correo="proveedor1@example.com",
        tipo_cuenta=TipoCuenta.LOCAL,
        password_hash=hashear_password("Clave123!"),
        rol_id=rol_id,
        unidad_negocio_id=None,
        activo=activo,
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


def test_login_local_exitoso_emite_tokens(db_session: Session, rol_un):
    _crear_usuario_local(db_session, rol_un.id)
    tokens = auth_service.login_local(db_session, "proveedor1", "Clave123!")
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"


def test_login_local_password_incorrecta(db_session: Session, rol_un):
    _crear_usuario_local(db_session, rol_un.id)
    with pytest.raises(CredencialesInvalidas):
        auth_service.login_local(db_session, "proveedor1", "ClaveIncorrecta")


def test_login_local_usuario_inexistente(db_session: Session):
    with pytest.raises(CredencialesInvalidas):
        auth_service.login_local(db_session, "no_existe", "Clave123!")


def test_login_local_usuario_inactivo(db_session: Session, rol_un):
    _crear_usuario_local(db_session, rol_un.id, activo=False)
    with pytest.raises(UsuarioInactivo):
        auth_service.login_local(db_session, "proveedor1", "Clave123!")


def test_refrescar_tokens_rota_y_revoca_el_anterior(db_session: Session, rol_un):
    usuario = _crear_usuario_local(db_session, rol_un.id)
    tokens = auth_service.login_local(db_session, "proveedor1", "Clave123!")

    nuevos_tokens = auth_service.refrescar_tokens(db_session, tokens.refresh_token)
    assert nuevos_tokens.refresh_token != tokens.refresh_token

    # El refresh token original ya fue rotado: reutilizarlo debe fallar (revocado).
    with pytest.raises(TokenInvalido):
        auth_service.refrescar_tokens(db_session, tokens.refresh_token)

    registros = db_session.query(TokenRefrescoRevocado).filter_by(usuario_id=usuario.id).all()
    assert any(r.revocado for r in registros)


def test_refrescar_tokens_con_token_invalido(db_session: Session):
    with pytest.raises(TokenInvalido):
        auth_service.refrescar_tokens(db_session, "token-no-valido")


def test_cerrar_sesion_revoca_el_refresh_token(db_session: Session, rol_un):
    _crear_usuario_local(db_session, rol_un.id)
    tokens = auth_service.login_local(db_session, "proveedor1", "Clave123!")

    auth_service.cerrar_sesion(db_session, tokens.refresh_token)

    with pytest.raises(TokenInvalido):
        auth_service.refrescar_tokens(db_session, tokens.refresh_token)
