"""
Primitivas de seguridad transversales (§4 de la especificación):

- Hashing de contraseñas con Argon2.
- Emisión y verificación de JWT (access + refresh).
- Cifrado AES-256-GCM a nivel de aplicación para campos sensibles (🔒 en §6).
"""
import base64
import os
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext

from app.core.config import obtener_configuracion

_contexto_password = CryptContext(schemes=["argon2"], deprecated="auto")


def hashear_password(password_plano: str) -> str:
    return _contexto_password.hash(password_plano)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    return _contexto_password.verify(password_plano, password_hash)


class TipoToken(str, Enum):
    ACCESO = "acceso"
    REFRESCO = "refresco"


def _clave_secreta() -> str:
    return obtener_configuracion().jwt_secret_key


def crear_token_acceso(
    *, usuario_id: int, username: str, rol: str, unidad_negocio_id: int | None, tipo_cuenta: str
) -> str:
    config = obtener_configuracion()
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "username": username,
        "rol": rol,
        "unidad_negocio_id": unidad_negocio_id,
        "tipo_cuenta": tipo_cuenta,
        "tipo_token": TipoToken.ACCESO.value,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=config.jwt_access_token_minutos),
    }
    return jwt.encode(payload, _clave_secreta(), algorithm=config.jwt_algorithm)


def crear_token_refresco(*, usuario_id: int) -> tuple[str, str, datetime]:
    """Crea un refresh token; retorna (token, jti, fecha_expiracion) para registrar en BD y permitir revocación."""
    config = obtener_configuracion()
    ahora = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    expiracion = ahora + timedelta(days=config.jwt_refresh_token_dias)
    payload = {
        "sub": str(usuario_id),
        "jti": jti,
        "tipo_token": TipoToken.REFRESCO.value,
        "iat": ahora,
        "exp": expiracion,
    }
    token = jwt.encode(payload, _clave_secreta(), algorithm=config.jwt_algorithm)
    return token, jti, expiracion


def decodificar_token(token: str) -> dict[str, Any]:
    """Lanza jwt.PyJWTError si el token es inválido/expiró. El llamador debe capturarla."""
    config = obtener_configuracion()
    return jwt.decode(token, _clave_secreta(), algorithms=[config.jwt_algorithm])


# --- Cifrado AES-256-GCM para columnas sensibles (🔒) ---

_TAMANO_NONCE_BYTES = 12


def _clave_aes() -> bytes:
    config = obtener_configuracion()
    clave = base64.urlsafe_b64decode(config.aes_master_key)
    if len(clave) != 32:
        raise ValueError("AES_MASTER_KEY debe decodificar a exactamente 32 bytes (AES-256).")
    return clave


def cifrar_valor(valor_plano: str) -> str:
    """Cifra un valor con AES-256-GCM. Retorna nonce + texto cifrado, codificado en base64."""
    aesgcm = AESGCM(_clave_aes())
    nonce = os.urandom(_TAMANO_NONCE_BYTES)
    cifrado = aesgcm.encrypt(nonce, valor_plano.encode("utf-8"), None)
    return base64.b64encode(nonce + cifrado).decode("utf-8")


def descifrar_valor(valor_cifrado: str) -> str:
    aesgcm = AESGCM(_clave_aes())
    datos = base64.b64decode(valor_cifrado)
    nonce, cifrado = datos[:_TAMANO_NONCE_BYTES], datos[_TAMANO_NONCE_BYTES:]
    return aesgcm.decrypt(nonce, cifrado, None).decode("utf-8")
