"""Endpoints de Novedad (§6.13, §7.6, §10): inspecciones, daños y mantenimientos,
con carga de fotografías geolocalizadas."""

from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.schemas.novedad import (
    FotografiaNovedadRespuesta,
    NovedadActualizar,
    NovedadCrear,
    NovedadRespuesta,
)
from app.services import novedad as servicio

router = APIRouter(prefix="/novedades", tags=["novedades"])


@router.get("", response_model=list[NovedadRespuesta])
def listar(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.listar(db, usuario)


@router.get("/{novedad_id}", response_model=NovedadRespuesta)
def obtener(
    novedad_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener(db, novedad_id, usuario)


@router.post("", response_model=NovedadRespuesta, status_code=201)
def crear(
    datos: NovedadCrear,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.crear(db, datos, usuario)


@router.put("/{novedad_id}", response_model=NovedadRespuesta)
def actualizar(
    novedad_id: int,
    datos: NovedadActualizar,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.actualizar(db, novedad_id, datos, usuario)


@router.post(
    "/{novedad_id}/fotografias", response_model=FotografiaNovedadRespuesta, status_code=201
)
async def subir_fotografia(
    novedad_id: int,
    archivo: UploadFile = File(...),
    latitud: Decimal | None = Form(None),
    longitud: Decimal | None = Form(None),
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    contenido = await archivo.read()
    return servicio.subir_fotografia(db, novedad_id, archivo, contenido, usuario, latitud, longitud)
