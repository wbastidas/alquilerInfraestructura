"""§6.1 UnidadNegocio: empresa eléctrica regional (Unidad de Negocio de CNEL EP)."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import AuditoriaMixin


class UnidadNegocio(Base, AuditoriaMixin):
    __tablename__ = "unidad_negocio"

    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    provincia: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(  # noqa: F821
        back_populates="unidad_negocio", foreign_keys="Usuario.unidad_negocio_id"
    )

    def __repr__(self) -> str:
        return f"<UnidadNegocio {self.codigo}>"
