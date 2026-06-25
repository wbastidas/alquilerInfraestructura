"""§6.15 LogAuditoria: registro completo de auditoría (§4.7), quién/qué/cuándo/desde dónde."""

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import AccionAuditoria
from app.models.mixins import AuditoriaMixin


class LogAuditoria(Base, AuditoriaMixin):
    __tablename__ = "log_auditoria"

    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    accion: Mapped[AccionAuditoria] = mapped_column(columna_enum(AccionAuditoria), nullable=False)
    entidad_tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    valores_antes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    valores_despues: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_origen: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    usuario: Mapped["Usuario | None"] = relationship(foreign_keys=[usuario_id])  # noqa: F821

    def __repr__(self) -> str:
        return f"<LogAuditoria {self.accion} {self.entidad_tipo}#{self.entidad_id}>"
