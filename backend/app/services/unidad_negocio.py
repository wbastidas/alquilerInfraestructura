"""Servicio de UnidadNegocio (§6.1). Catálogo global: cualquier usuario autenticado
puede listarlo (es la base del modelo Matriz/UN); solo SUPERADMIN lo administra."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import RecursoNoEncontrado
from app.models.unidad_negocio import UnidadNegocio
from app.schemas.unidad_negocio import UnidadNegocioActualizar, UnidadNegocioCrear


def listar(db: Session) -> list[UnidadNegocio]:
    return list(db.scalars(select(UnidadNegocio).order_by(UnidadNegocio.nombre)))


def obtener(db: Session, unidad_negocio_id: int) -> UnidadNegocio:
    unidad = db.get(UnidadNegocio, unidad_negocio_id)
    if unidad is None:
        raise RecursoNoEncontrado("Unidad de Negocio no encontrada.")
    return unidad


def crear(db: Session, datos: UnidadNegocioCrear) -> UnidadNegocio:
    unidad = UnidadNegocio(**datos.model_dump())
    db.add(unidad)
    db.commit()
    db.refresh(unidad)
    return unidad


def actualizar(db: Session, unidad_negocio_id: int, datos: UnidadNegocioActualizar) -> UnidadNegocio:
    unidad = obtener(db, unidad_negocio_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(unidad, campo, valor)
    db.commit()
    db.refresh(unidad)
    return unidad
