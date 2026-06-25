"""Endpoints de CableOperadora (§6.4, §10), con alcance por UN (§5.2)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.schemas.cable_operadora import (
    CableOperadoraActualizar,
    CableOperadoraCrear,
    CableOperadoraRespuesta,
)
from app.services import cable_operadora as servicio

router = APIRouter(prefix="/operadoras", tags=["operadoras"])


@router.get("", response_model=list[CableOperadoraRespuesta])
def listar(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.listar(db, usuario)


@router.get("/{operadora_id}", response_model=CableOperadoraRespuesta)
def obtener(
    operadora_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener(db, operadora_id, usuario)


@router.post("", response_model=CableOperadoraRespuesta, status_code=201)
def crear(
    datos: CableOperadoraCrear,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.crear(db, datos, usuario)


@router.put("/{operadora_id}", response_model=CableOperadoraRespuesta)
def actualizar(
    operadora_id: int,
    datos: CableOperadoraActualizar,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.actualizar(db, operadora_id, datos, usuario)
