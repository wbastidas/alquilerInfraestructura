"""Servicio de CableOperadora (§6.4, §7.1), con filtro de alcance por UN (§5.2)."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UsuarioContexto
from app.core.exceptions import RecursoNoEncontrado
from app.models.cable_operadora import (
    CableOperadora,
    NombreComercial,
    ResponsableTecnicoZona,
    TelefonoOperadora,
)
from app.schemas.cable_operadora import CableOperadoraActualizar, CableOperadoraCrear
from app.services.base import aplicar_alcance_un, verificar_pertenece_a_un

_CARGA_RELACIONES = (
    selectinload(CableOperadora.nombres_comerciales),
    selectinload(CableOperadora.telefonos),
    selectinload(CableOperadora.responsables_tecnicos),
)


def listar(db: Session, usuario_actual: UsuarioContexto) -> list[CableOperadora]:
    query = select(CableOperadora).options(*_CARGA_RELACIONES).order_by(CableOperadora.nombre_empresa)
    query = aplicar_alcance_un(query, CableOperadora.unidad_negocio_id, usuario_actual)
    return list(db.scalars(query))


def obtener(db: Session, operadora_id: int, usuario_actual: UsuarioContexto) -> CableOperadora:
    query = (
        select(CableOperadora)
        .options(*_CARGA_RELACIONES)
        .where(CableOperadora.id == operadora_id)
    )
    operadora = db.scalar(query)
    if operadora is None:
        raise RecursoNoEncontrado("Operadora no encontrada.")
    verificar_pertenece_a_un(usuario_actual, operadora.unidad_negocio_id)
    return operadora


def crear(db: Session, datos: CableOperadoraCrear, usuario_actual: UsuarioContexto) -> CableOperadora:
    verificar_pertenece_a_un(usuario_actual, datos.unidad_negocio_id)
    campos = datos.model_dump(
        exclude={"nombres_comerciales", "telefonos", "responsables_tecnicos"}
    )
    operadora = CableOperadora(**campos)
    operadora.nombres_comerciales = [
        NombreComercial(**n.model_dump()) for n in datos.nombres_comerciales
    ]
    operadora.telefonos = [TelefonoOperadora(**t.model_dump()) for t in datos.telefonos]
    operadora.responsables_tecnicos = [
        ResponsableTecnicoZona(**r.model_dump()) for r in datos.responsables_tecnicos
    ]
    db.add(operadora)
    db.commit()
    db.refresh(operadora)
    return operadora


def actualizar(
    db: Session,
    operadora_id: int,
    datos: CableOperadoraActualizar,
    usuario_actual: UsuarioContexto,
) -> CableOperadora:
    operadora = obtener(db, operadora_id, usuario_actual)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(operadora, campo, valor)
    db.commit()
    db.refresh(operadora)
    return operadora
