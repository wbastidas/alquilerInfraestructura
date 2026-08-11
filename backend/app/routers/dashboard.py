"""Endpoint de Dashboard consolidado (§7.2, §10)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual
from app.db.session import obtener_db
from app.schemas.dashboard import DashboardConsolidado
from app.services import dashboard as servicio

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/consolidado", response_model=DashboardConsolidado)
def consolidado(
    anio: int | None = None,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener_consolidado(db, usuario, anio)
