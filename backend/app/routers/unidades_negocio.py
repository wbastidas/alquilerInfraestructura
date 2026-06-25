"""Endpoints de UnidadNegocio (§6.1, §10). Catálogo global de lectura; administración
restringida a SUPERADMIN."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import obtener_usuario_actual, requerir_roles
from app.db.session import obtener_db
from app.schemas.unidad_negocio import (
    UnidadNegocioActualizar,
    UnidadNegocioCrear,
    UnidadNegocioRespuesta,
)
from app.services import unidad_negocio as servicio

router = APIRouter(prefix="/unidades-negocio", tags=["unidades de negocio"])


@router.get(
    "", response_model=list[UnidadNegocioRespuesta], dependencies=[Depends(obtener_usuario_actual)]
)
def listar(db: Session = Depends(obtener_db)):
    return servicio.listar(db)


@router.get(
    "/{unidad_negocio_id}",
    response_model=UnidadNegocioRespuesta,
    dependencies=[Depends(obtener_usuario_actual)],
)
def obtener(unidad_negocio_id: int, db: Session = Depends(obtener_db)):
    return servicio.obtener(db, unidad_negocio_id)


@router.post(
    "",
    response_model=UnidadNegocioRespuesta,
    status_code=201,
    dependencies=[Depends(requerir_roles("SUPERADMIN"))],
)
def crear(datos: UnidadNegocioCrear, db: Session = Depends(obtener_db)):
    return servicio.crear(db, datos)


@router.put(
    "/{unidad_negocio_id}",
    response_model=UnidadNegocioRespuesta,
    dependencies=[Depends(requerir_roles("SUPERADMIN"))],
)
def actualizar(
    unidad_negocio_id: int, datos: UnidadNegocioActualizar, db: Session = Depends(obtener_db)
):
    return servicio.actualizar(db, unidad_negocio_id, datos)
