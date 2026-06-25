"""Servicio de Usuario (§6.2), con filtro de alcance por Unidad de Negocio (§5.2)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto
from app.core.exceptions import RecursoNoEncontrado
from app.core.security import hashear_password
from app.models.enums import TipoCuenta
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioActualizar, UsuarioCrear
from app.services.base import aplicar_alcance_un, verificar_pertenece_a_un


def listar(db: Session, usuario_actual: UsuarioContexto) -> list[Usuario]:
    query = select(Usuario).order_by(Usuario.username)
    query = aplicar_alcance_un(query, Usuario.unidad_negocio_id, usuario_actual)
    return list(db.scalars(query))


def obtener(db: Session, usuario_id: int, usuario_actual: UsuarioContexto) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise RecursoNoEncontrado("Usuario no encontrado.")
    verificar_pertenece_a_un(usuario_actual, usuario.unidad_negocio_id)
    return usuario


def crear(db: Session, datos: UsuarioCrear) -> Usuario:
    password_hash = None
    if datos.tipo_cuenta in (TipoCuenta.LOCAL, TipoCuenta.PROVEEDOR):
        if not datos.password:
            raise ValueError("Las cuentas LOCAL/PROVEEDOR requieren contraseña.")
        password_hash = hashear_password(datos.password)

    usuario = Usuario(
        username=datos.username,
        nombre_completo=datos.nombre_completo,
        correo=datos.correo,
        tipo_cuenta=datos.tipo_cuenta,
        password_hash=password_hash,
        rol_id=datos.rol_id,
        unidad_negocio_id=datos.unidad_negocio_id,
        cable_operadora_id=datos.cable_operadora_id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar(
    db: Session, usuario_id: int, datos: UsuarioActualizar, usuario_actual: UsuarioContexto
) -> Usuario:
    usuario = obtener(db, usuario_id, usuario_actual)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario
