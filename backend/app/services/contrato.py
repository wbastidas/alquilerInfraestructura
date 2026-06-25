"""Servicio de Contrato (§6.5, §7.1), con filtro de alcance por UN (§5.2) y
transiciones de estado controladas.

Transiciones permitidas (§7.1):
    EN_JURIDICO -> VIGENTE
    VIGENTE -> EN_RENOVACION
    EN_RENOVACION -> VIGENTE
    EN_RENOVACION -> TERMINADO
    VIGENTE -> SUSPENDIDO
    SUSPENDIDO -> VIGENTE
    VIGENTE -> EN_JURIDICO
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UsuarioContexto
from app.core.exceptions import RecursoNoEncontrado, TransicionInvalida
from app.models.contrato import Contrato
from app.models.enums import EstadoContrato
from app.schemas.contrato import ContratoActualizar, ContratoCrear
from app.services.base import aplicar_alcance_un, verificar_pertenece_a_un

_CARGA_RELACIONES = (selectinload(Contrato.cable_operadora), selectinload(Contrato.unidad_negocio))

_TRANSICIONES_PERMITIDAS: dict[EstadoContrato, set[EstadoContrato]] = {
    EstadoContrato.EN_JURIDICO: {EstadoContrato.VIGENTE},
    EstadoContrato.VIGENTE: {
        EstadoContrato.EN_RENOVACION,
        EstadoContrato.SUSPENDIDO,
        EstadoContrato.EN_JURIDICO,
    },
    EstadoContrato.EN_RENOVACION: {EstadoContrato.VIGENTE, EstadoContrato.TERMINADO},
    EstadoContrato.SUSPENDIDO: {EstadoContrato.VIGENTE},
    EstadoContrato.TERMINADO: set(),
}


def _validar_transicion(actual: EstadoContrato, nuevo: EstadoContrato) -> None:
    if actual == nuevo:
        return
    if nuevo not in _TRANSICIONES_PERMITIDAS.get(actual, set()):
        raise TransicionInvalida(f"No se permite transicionar de {actual.value} a {nuevo.value}.")


def listar(db: Session, usuario_actual: UsuarioContexto) -> list[Contrato]:
    query = select(Contrato).options(*_CARGA_RELACIONES).order_by(Contrato.numero_contrato)
    query = aplicar_alcance_un(query, Contrato.unidad_negocio_id, usuario_actual)
    return list(db.scalars(query))


def obtener(db: Session, contrato_id: int, usuario_actual: UsuarioContexto) -> Contrato:
    query = select(Contrato).options(*_CARGA_RELACIONES).where(Contrato.id == contrato_id)
    contrato = db.scalar(query)
    if contrato is None:
        raise RecursoNoEncontrado("Contrato no encontrado.")
    verificar_pertenece_a_un(usuario_actual, contrato.unidad_negocio_id)
    return contrato


def crear(db: Session, datos: ContratoCrear, usuario_actual: UsuarioContexto) -> Contrato:
    verificar_pertenece_a_un(usuario_actual, datos.unidad_negocio_id)
    contrato = Contrato(**datos.model_dump())
    db.add(contrato)
    db.commit()
    db.refresh(contrato)
    return contrato


def actualizar(
    db: Session, contrato_id: int, datos: ContratoActualizar, usuario_actual: UsuarioContexto
) -> Contrato:
    contrato = obtener(db, contrato_id, usuario_actual)
    cambios = datos.model_dump(exclude_unset=True)
    nuevo_estado = cambios.pop("estado", None)
    if nuevo_estado is not None:
        _validar_transicion(contrato.estado, nuevo_estado)
        contrato.estado = nuevo_estado
    for campo, valor in cambios.items():
        setattr(contrato, campo, valor)
    db.commit()
    db.refresh(contrato)
    return contrato
