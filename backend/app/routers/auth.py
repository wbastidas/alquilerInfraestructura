"""Endpoints de autenticación (§5.1, §10): doble vía local/dominio + refresh + logout."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import service as auth_service
from app.auth.deps import UsuarioContexto, obtener_usuario_actual
from app.auditoria.servicio import registrar_auditoria
from app.core.exceptions import CredencialesInvalidas, TokenInvalido, UsuarioInactivo
from app.db.session import obtener_db
from app.middlewares.rate_limit import limiter
from app.models.enums import AccionAuditoria
from app.schemas.auth import LoginDominioRequest, LoginLocalRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, datos: LoginLocalRequest, db: Session = Depends(obtener_db)):
    """Login con usuario/clave local (proveedores y cuentas de respaldo)."""
    try:
        tokens = auth_service.login_local(db, datos.username, datos.password)
    except (CredencialesInvalidas, UsuarioInactivo) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    registrar_auditoria(
        db,
        usuario_id=None,
        accion=AccionAuditoria.LOGIN,
        entidad_tipo="Usuario",
        descripcion=f"Login local: {datos.username}",
        ip_origen=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return tokens


@router.post("/login/ad", response_model=TokenResponse)
@limiter.limit("5/minute")
def login_dominio(request: Request, datos: LoginDominioRequest, db: Session = Depends(obtener_db)):
    """Login contra dominio Windows / Active Directory (funcionarios CNEL EP)."""
    try:
        tokens = auth_service.login_dominio(db, datos.username, datos.password)
    except (CredencialesInvalidas, UsuarioInactivo) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    registrar_auditoria(
        db,
        usuario_id=None,
        accion=AccionAuditoria.LOGIN,
        entidad_tipo="Usuario",
        descripcion=f"Login dominio: {datos.username}",
        ip_origen=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refrescar(datos: RefreshRequest, db: Session = Depends(obtener_db)):
    try:
        return auth_service.refrescar_tokens(db, datos.refresh_token)
    except TokenInvalido as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    datos: RefreshRequest,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    auth_service.cerrar_sesion(db, datos.refresh_token)
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        accion=AccionAuditoria.LOGOUT,
        entidad_tipo="Usuario",
        entidad_id=usuario.id,
    )
    db.commit()
