"""Endpoint de Rol (§2.1, §6.3). Catálogo global de solo lectura, accesible a
cualquier usuario autenticado (base para selectores de rol en formularios de
alta de Usuario)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import obtener_usuario_actual
from app.db.session import obtener_db
from app.schemas.rol import RolRespuesta
from app.services import rol as servicio

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RolRespuesta], dependencies=[Depends(obtener_usuario_actual)])
def listar(db: Session = Depends(obtener_db)):
    return servicio.listar(db)
