"""§6.14 Alerta: vencimientos de contrato, póliza, pago o título habilitante."""
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import SeveridadAlerta, TipoAlerta
from app.models.mixins import AuditoriaMixin


class Alerta(Base, AuditoriaMixin):
    __tablename__ = "alerta"

    tipo: Mapped[TipoAlerta] = mapped_column(columna_enum(TipoAlerta), nullable=False)
    # Tipo de entidad referenciada (CONTRATO, FACTURA, OPERADORA, etc.); no se restringe a un
    # enum cerrado porque Alerta puede apuntar a cualquier entidad del modelo.
    entidad_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad_id: Mapped[int] = mapped_column(nullable=False, index=True)
    unidad_negocio_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidad_negocio.id"), nullable=True
    )
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[SeveridadAlerta] = mapped_column(
        columna_enum(SeveridadAlerta), nullable=False, default=SeveridadAlerta.INFO
    )
    fecha_generacion: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    leida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    unidad_negocio: Mapped["UnidadNegocio | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Alerta {self.tipo} severidad={self.severidad}>"
