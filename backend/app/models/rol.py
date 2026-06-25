"""§6.3 Rol / Permiso / RolPermiso: base del sistema RBAC (§5.3)."""
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import AuditoriaMixin


class Rol(Base, AuditoriaMixin):
    __tablename__ = "rol"

    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    permisos: Mapped[list["RolPermiso"]] = relationship(back_populates="rol")

    def __repr__(self) -> str:
        return f"<Rol {self.codigo}>"


class Permiso(Base, AuditoriaMixin):
    __tablename__ = "permiso"

    codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Permiso {self.codigo}>"


class RolPermiso(Base, AuditoriaMixin):
    __tablename__ = "rol_permiso"
    __table_args__ = (UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permiso"),)

    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"), nullable=False)
    permiso_id: Mapped[int] = mapped_column(ForeignKey("permiso.id"), nullable=False)

    rol: Mapped["Rol"] = relationship(back_populates="permisos")
    permiso: Mapped["Permiso"] = relationship()
