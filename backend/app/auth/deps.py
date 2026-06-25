"""Dependencias de FastAPI para autenticación y RBAC (§5.2, §5.3).

Regla de oro reforzada en backend (no solo UI):
- Matriz (`MATRIZ_CONSULTA`) = solo lectura global.
- Unidad de Negocio (`UN_*`) = lectura/escritura de su propia UN.
- Proveedor (`PROVEEDOR`) = lectura/escritura de su propio expediente.
"""
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decodificar_token

_bearer = HTTPBearer(auto_error=True)


@dataclass(frozen=True)
class UsuarioContexto:
    """Identidad derivada del access token, sin volver a consultar la BD en cada request."""

    id: int
    username: str
    rol: str
    unidad_negocio_id: int | None
    tipo_cuenta: str

    @property
    def es_matriz_o_superadmin(self) -> bool:
        return self.rol in {"MATRIZ_CONSULTA", "SUPERADMIN"}

    @property
    def es_proveedor(self) -> bool:
        return self.rol == "PROVEEDOR"


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(_bearer),
) -> UsuarioContexto:
    try:
        payload = decodificar_token(credenciales.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="El token ha expirado."
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido."
        ) from exc

    if payload.get("tipo_token") != "acceso":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un access token, no un refresh token.",
        )

    return UsuarioContexto(
        id=int(payload["sub"]),
        username=payload["username"],
        rol=payload["rol"],
        unidad_negocio_id=payload.get("unidad_negocio_id"),
        tipo_cuenta=payload["tipo_cuenta"],
    )


def requerir_roles(*roles_permitidos: str):
    """Dependencia que exige que el usuario tenga uno de los roles indicados."""

    def verificador(usuario: UsuarioContexto = Depends(obtener_usuario_actual)) -> UsuarioContexto:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes para esta operación.",
            )
        return usuario

    return verificador


def requerir_escritura(
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
) -> UsuarioContexto:
    """Bloquea cualquier operación de escritura para Matriz (solo lectura, §5.2)."""
    if usuario.es_matriz_o_superadmin and usuario.rol == "MATRIZ_CONSULTA":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El rol Matriz tiene acceso de solo lectura; no puede crear, editar ni eliminar.",
        )
    return usuario


def filtro_unidad_negocio(usuario: UsuarioContexto) -> int | None:
    """Retorna el `unidad_negocio_id` por el cual debe filtrarse la consulta, o `None` si el
    usuario tiene alcance global (Matriz/Superadmin) y no debe restringirse."""
    if usuario.es_matriz_o_superadmin:
        return None
    return usuario.unidad_negocio_id
