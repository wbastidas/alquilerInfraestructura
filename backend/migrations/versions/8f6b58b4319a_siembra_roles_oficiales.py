"""siembra roles oficiales

Revision ID: 8f6b58b4319a
Revises: f4116961e7ad
Create Date: 2026-06-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f6b58b4319a"
down_revision: Union[str, Sequence[str], None] = "f4116961e7ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Los 9 roles oficiales del sistema (§2.1 de la especificación técnica).
ROLES = [
    ("MATRIZ_CONSULTA", "Matriz (solo lectura)", "Solo lectura de todo (dashboards, reportes consolidados)."),
    ("UN_ADMIN", "Administrador de Unidad de Negocio", "Lectura/escritura total dentro de su UN."),
    ("UN_ADMIN_CONTRATO", "Administrador de Contratos de UN", "Gestiona contratos asignados, autoriza ampliaciones."),
    ("UN_DELEGADO_COORDINADOR", "Delegado Coordinador de UN", "Recibe y deriva solicitudes de proveedores sin contrato."),
    ("UN_DELEGADO_TECNICO", "Delegado Técnico de UN", "Revisión técnica, informe de factibilidad, registro de novedades."),
    ("UN_GERENTE", "Gerente de UN", "Aprobación gerencial."),
    ("UN_JURIDICO", "Jurídico de UN", "Genera/valida contrato a partir del modelo base."),
    ("PROVEEDOR", "Proveedor", "Portal externo: crea solicitudes, sube documentos, ve estado."),
    ("SUPERADMIN", "Super Administrador", "Configuración, catálogos, parámetros, gestión de usuarios."),
]

rol_tabla = sa.table(
    "rol",
    sa.column("codigo", sa.String),
    sa.column("nombre", sa.String),
    sa.column("descripcion", sa.Text),
)


def upgrade() -> None:
    op.bulk_insert(
        rol_tabla,
        [{"codigo": codigo, "nombre": nombre, "descripcion": descripcion} for codigo, nombre, descripcion in ROLES],
    )


def downgrade() -> None:
    codigos = tuple(codigo for codigo, _, _ in ROLES)
    op.execute(rol_tabla.delete().where(rol_tabla.c.codigo.in_(codigos)))
