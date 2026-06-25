"""§6.2 Usuario: cuenta de acceso al sistema (funcionario CNEL EP o proveedor)."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import TipoCuenta
from app.models.mixins import AuditoriaMixin


class Usuario(Base, AuditoriaMixin):
    __tablename__ = "usuario"

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    correo: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_cuenta: Mapped[TipoCuenta] = mapped_column(columna_enum(TipoCuenta), nullable=False)
    # Nulo para cuentas AD: la contraseña la valida el dominio (LDAP), no el sistema.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"), nullable=False)
    unidad_negocio_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidad_negocio.id"), nullable=True
    )
    cable_operadora_id: Mapped[int | None] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=True
    )

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(nullable=True)

    rol: Mapped["Rol"] = relationship(foreign_keys=[rol_id])  # noqa: F821
    unidad_negocio: Mapped["UnidadNegocio | None"] = relationship(  # noqa: F821
        back_populates="usuarios", foreign_keys=[unidad_negocio_id]
    )
    cable_operadora: Mapped["CableOperadora | None"] = relationship(  # noqa: F821
        foreign_keys=[cable_operadora_id]
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.username}>"
