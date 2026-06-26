"""Endpoints de Solicitud y su workflow de autorizaciones (§6.7, §7.3, §7.5, §8, §10)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.schemas.autorizacion import AutorizacionDecision, AutorizacionRespuesta
from app.schemas.solicitud import SolicitudActualizar, SolicitudCrear, SolicitudRespuesta
from app.services import solicitud as servicio

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])


@router.get("", response_model=list[SolicitudRespuesta])
def listar(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.listar(db, usuario)


@router.get("/{solicitud_id}", response_model=SolicitudRespuesta)
def obtener(
    solicitud_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener(db, solicitud_id, usuario)


@router.get("/{solicitud_id}/autorizaciones", response_model=list[AutorizacionRespuesta])
def listar_autorizaciones(
    solicitud_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.listar_autorizaciones(db, solicitud_id, usuario)


@router.post("", response_model=SolicitudRespuesta, status_code=201)
def crear(
    datos: SolicitudCrear,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.crear(db, datos, usuario)


@router.put("/{solicitud_id}", response_model=SolicitudRespuesta)
def actualizar(
    solicitud_id: int,
    datos: SolicitudActualizar,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.actualizar(db, solicitud_id, datos, usuario)


@router.post("/{solicitud_id}/enviar", response_model=SolicitudRespuesta)
def enviar(
    solicitud_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.enviar(db, solicitud_id, usuario)


@router.post("/{solicitud_id}/decidir", response_model=SolicitudRespuesta)
def decidir(
    solicitud_id: int,
    datos: AutorizacionDecision,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.decidir(db, solicitud_id, datos, usuario)


@router.post("/{solicitud_id}/reenviar", response_model=SolicitudRespuesta)
def reenviar(
    solicitud_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.reenviar(db, solicitud_id, usuario)
