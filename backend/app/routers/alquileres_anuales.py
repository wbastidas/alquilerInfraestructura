"""Endpoints de AlquilerAnual (§6.6, §7.2, §10), con alcance por UN (§5.2)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.schemas.alquiler_anual import (
    AlquilerAnualActualizar,
    AlquilerAnualCrear,
    AlquilerAnualRespuesta,
)
from app.services import alquiler_anual as servicio

router = APIRouter(prefix="/alquileres-anuales", tags=["alquileres anuales"])


@router.get("", response_model=list[AlquilerAnualRespuesta])
def listar(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.listar(db, usuario)


@router.get("/{alquiler_anual_id}", response_model=AlquilerAnualRespuesta)
def obtener(
    alquiler_anual_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener(db, alquiler_anual_id, usuario)


@router.post("", response_model=AlquilerAnualRespuesta, status_code=201)
def crear(
    datos: AlquilerAnualCrear,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.crear(db, datos, usuario)


@router.put("/{alquiler_anual_id}", response_model=AlquilerAnualRespuesta)
def actualizar(
    alquiler_anual_id: int,
    datos: AlquilerAnualActualizar,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.actualizar(db, alquiler_anual_id, datos, usuario)
