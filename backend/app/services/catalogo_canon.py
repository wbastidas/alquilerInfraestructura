"""Servicio de CatalogoCanon (§6.12). Catálogo global: lectura para cualquier
usuario autenticado; la escritura se restringe a SUPERADMIN a nivel de router."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import RecursoNoEncontrado
from app.models.catalogo_canon import CatalogoCanon
from app.schemas.catalogo_canon import CatalogoCanonCrear


def listar(db: Session) -> list[CatalogoCanon]:
    query = select(CatalogoCanon).order_by(
        CatalogoCanon.tipo_zona, CatalogoCanon.vigente_desde.desc()
    )
    return list(db.scalars(query))


def obtener(db: Session, catalogo_canon_id: int) -> CatalogoCanon:
    catalogo = db.get(CatalogoCanon, catalogo_canon_id)
    if catalogo is None:
        raise RecursoNoEncontrado("Valor de canon no encontrado.")
    return catalogo


def crear(db: Session, datos: CatalogoCanonCrear) -> CatalogoCanon:
    catalogo = CatalogoCanon(**datos.model_dump())
    db.add(catalogo)
    db.commit()
    db.refresh(catalogo)
    return catalogo
