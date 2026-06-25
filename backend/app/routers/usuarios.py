"""Endpoints de Usuario (§6.2, §10). Listado/edición con alcance por UN (§5.2);
la creación de cuentas la administra SUPERADMIN."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import (
    UsuarioContexto,
    obtener_usuario_actual,
    requerir_escritura,
    requerir_roles,
)
from app.db.session import obtener_db
from app.schemas.usuario import UsuarioActualizar, UsuarioCrear, UsuarioRespuesta
from app.services import usuario as servicio

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioRespuesta])
def listar(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.listar(db, usuario)


@router.get("/{usuario_id}", response_model=UsuarioRespuesta)
def obtener(
    usuario_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener(db, usuario_id, usuario)


@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=201,
    dependencies=[Depends(requerir_roles("SUPERADMIN"))],
)
def crear(datos: UsuarioCrear, db: Session = Depends(obtener_db)):
    return servicio.crear(db, datos)


@router.put("/{usuario_id}", response_model=UsuarioRespuesta)
def actualizar(
    usuario_id: int,
    datos: UsuarioActualizar,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.actualizar(db, usuario_id, datos, usuario)
