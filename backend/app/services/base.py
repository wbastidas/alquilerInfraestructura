"""Filtro de seguridad por Unidad de Negocio (§5.2), reforzado a nivel de servicio.

Regla de oro: Matriz/Superadmin = lectura global; UN = lectura/escritura solo de
registros con su propio `unidad_negocio_id`. Esto se aplica aquí (no solo en la UI)
para cumplir el criterio de aceptación de §14.
"""
from sqlalchemy import Select

from app.auth.deps import UsuarioContexto
from app.core.exceptions import PermisoDenegado


def aplicar_alcance_un(query: Select, columna_unidad_negocio, usuario: UsuarioContexto) -> Select:
    """Restringe un SELECT a la UN del usuario, salvo que tenga alcance global."""
    if usuario.es_matriz_o_superadmin:
        return query
    return query.where(columna_unidad_negocio == usuario.unidad_negocio_id)


def verificar_pertenece_a_un(usuario: UsuarioContexto, unidad_negocio_id: int | None) -> None:
    """Lanza `PermisoDenegado` si una UN intenta acceder/editar un registro de otra UN."""
    if usuario.es_matriz_o_superadmin:
        return
    if usuario.unidad_negocio_id != unidad_negocio_id:
        raise PermisoDenegado("No tiene acceso a registros de otra Unidad de Negocio.")
