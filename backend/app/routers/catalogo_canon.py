"""Endpoints de CatalogoCanon (§6.12, §10). Catálogo global de lectura; la
escritura se restringe a SUPERADMIN (define los valores normativos del canon)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import obtener_usuario_actual, requerir_roles
from app.db.session import obtener_db
from app.schemas.catalogo_canon import CatalogoCanonCrear, CatalogoCanonRespuesta
from app.services import catalogo_canon as servicio

router = APIRouter(prefix="/catalogo-canon", tags=["catálogo de canon"])


@router.get(
    "", response_model=list[CatalogoCanonRespuesta], dependencies=[Depends(obtener_usuario_actual)]
)
def listar(db: Session = Depends(obtener_db)):
    return servicio.listar(db)


@router.get(
    "/{catalogo_canon_id}",
    response_model=CatalogoCanonRespuesta,
    dependencies=[Depends(obtener_usuario_actual)],
)
def obtener(catalogo_canon_id: int, db: Session = Depends(obtener_db)):
    return servicio.obtener(db, catalogo_canon_id)


@router.post(
    "",
    response_model=CatalogoCanonRespuesta,
    status_code=201,
    dependencies=[Depends(requerir_roles("SUPERADMIN"))],
)
def crear(datos: CatalogoCanonCrear, db: Session = Depends(obtener_db)):
    return servicio.crear(db, datos)
