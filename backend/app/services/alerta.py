"""Servicio de Alerta (§6.14, §7.2, §7.4): vencimientos y morosidad generados
por los jobs programados.

Es una herramienta de gestión interna de CNEL EP: alcance por rol igual al
resto del sistema (Matriz/Superadmin = lectura global, UN = solo su propia
UN), pero el Proveedor no tiene acceso, ya que estas alertas no forman parte
de su expediente sino del seguimiento administrativo interno.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto
from app.core.exceptions import PermisoDenegado, RecursoNoEncontrado
from app.models.alerta import Alerta
from app.services.base import aplicar_alcance_un, verificar_pertenece_a_un


def listar(db: Session, usuario_actual: UsuarioContexto) -> list[Alerta]:
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no tiene acceso a las alertas internas.")
    query = select(Alerta).order_by(Alerta.fecha_generacion.desc())
    query = aplicar_alcance_un(query, Alerta.unidad_negocio_id, usuario_actual)
    return list(db.scalars(query))


def marcar_leida(db: Session, alerta_id: int, usuario_actual: UsuarioContexto) -> Alerta:
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no tiene acceso a las alertas internas.")

    alerta = db.get(Alerta, alerta_id)
    if alerta is None:
        raise RecursoNoEncontrado("Alerta no encontrada.")
    verificar_pertenece_a_un(usuario_actual, alerta.unidad_negocio_id)

    alerta.leida = True
    db.commit()
    db.refresh(alerta)
    return alerta
