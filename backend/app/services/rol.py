"""Servicio de Rol (§2.1, §6.3). Catálogo de solo lectura: los 9 roles oficiales
se siembran por migración; no hay alta/edición en runtime."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rol import Rol


def listar(db: Session) -> list[Rol]:
    return list(db.scalars(select(Rol).order_by(Rol.nombre)))
