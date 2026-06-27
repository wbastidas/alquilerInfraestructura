"""Endpoints de Alerta (§6.14, §10): vencimientos y morosidad."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.schemas.alerta import AlertaRespuesta
from app.services import alerta as servicio

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=list[AlertaRespuesta])
def listar(
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.listar(db, usuario)


@router.patch("/{alerta_id}/leida", response_model=AlertaRespuesta)
def marcar_leida(
    alerta_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.marcar_leida(db, alerta_id, usuario)
