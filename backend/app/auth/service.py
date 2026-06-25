"""Servicio de autenticación: doble vía (local/AD) + emisión, refresco y revocación de JWT (§5.1, §4.1)."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.ldap_client import autenticar_contra_dominio
from app.core.exceptions import CredencialesInvalidas, TokenInvalido, UsuarioInactivo
from app.core.security import (
    crear_token_acceso,
    crear_token_refresco,
    decodificar_token,
    verificar_password,
)
from app.models.enums import TipoCuenta
from app.models.rol import Rol
from app.models.token_refresco import TokenRefrescoRevocado
from app.models.usuario import Usuario
from app.schemas.auth import TokenResponse


def _emitir_tokens(db: Session, usuario: Usuario) -> TokenResponse:
    rol: Rol = usuario.rol
    access_token = crear_token_acceso(
        usuario_id=usuario.id,
        username=usuario.username,
        rol=rol.codigo,
        unidad_negocio_id=usuario.unidad_negocio_id,
        tipo_cuenta=usuario.tipo_cuenta.value,
    )
    refresh_token, jti, expiracion = crear_token_refresco(usuario_id=usuario.id)
    db.add(
        TokenRefrescoRevocado(
            jti=jti, usuario_id=usuario.id, expira_en=expiracion, revocado=False
        )
    )
    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def login_local(db: Session, username: str, password: str) -> TokenResponse:
    """Login con usuario/clave local (proveedores y cuentas de respaldo)."""
    usuario = db.scalar(
        select(Usuario).where(
            Usuario.username == username,
            Usuario.tipo_cuenta.in_([TipoCuenta.LOCAL, TipoCuenta.PROVEEDOR]),
        )
    )
    if usuario is None or not usuario.password_hash:
        raise CredencialesInvalidas("Usuario o contraseña incorrectos.")
    if not verificar_password(password, usuario.password_hash):
        raise CredencialesInvalidas("Usuario o contraseña incorrectos.")
    if not usuario.activo:
        raise UsuarioInactivo("La cuenta de usuario está inactiva.")
    return _emitir_tokens(db, usuario)


def login_dominio(db: Session, username: str, password: str) -> TokenResponse:
    """Login contra dominio Windows / Active Directory (funcionarios CNEL EP)."""
    if not autenticar_contra_dominio(username, password):
        raise CredencialesInvalidas("Usuario o contraseña de dominio incorrectos.")
    usuario = db.scalar(
        select(Usuario).where(Usuario.username == username, Usuario.tipo_cuenta == TipoCuenta.AD)
    )
    if usuario is None:
        # El usuario existe en AD pero no ha sido provisionado en el sistema con un rol/UN.
        raise CredencialesInvalidas(
            "Usuario autenticado en el dominio pero no registrado en SGAIE. "
            "Contacte al administrador para asignarle un rol."
        )
    if not usuario.activo:
        raise UsuarioInactivo("La cuenta de usuario está inactiva.")
    return _emitir_tokens(db, usuario)


def refrescar_tokens(db: Session, refresh_token: str) -> TokenResponse:
    """Valida y rota un refresh token (§4.1): revoca el anterior y emite uno nuevo."""
    try:
        payload = decodificar_token(refresh_token)
    except Exception as exc:  # jwt.PyJWTError y subclases
        raise TokenInvalido("Refresh token inválido o expirado.") from exc

    if payload.get("tipo_token") != "refresco":
        raise TokenInvalido("El token proporcionado no es un refresh token.")

    jti = payload.get("jti")
    registro = db.scalar(select(TokenRefrescoRevocado).where(TokenRefrescoRevocado.jti == jti))
    if registro is None or registro.revocado:
        raise TokenInvalido("Refresh token revocado o desconocido.")

    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise TokenInvalido("Usuario no encontrado o inactivo.")

    registro.revocado = True  # rotación: el token usado queda inutilizable
    db.commit()
    return _emitir_tokens(db, usuario)


def cerrar_sesion(db: Session, refresh_token: str) -> None:
    """Revoca el refresh token (logout)."""
    try:
        payload = decodificar_token(refresh_token)
    except Exception:
        return  # token ya inválido: nada que revocar
    jti = payload.get("jti")
    registro = db.scalar(select(TokenRefrescoRevocado).where(TokenRefrescoRevocado.jti == jti))
    if registro is not None:
        registro.revocado = True
        db.commit()
