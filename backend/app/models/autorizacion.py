"""§6.10 Autorizacion: paso del workflow multinivel (§8), con adjuntos."""

from datetime import date

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import EstadoAutorizacion, EtapaAutorizacion
from app.models.mixins import AuditoriaMixin


class Autorizacion(Base, AuditoriaMixin):
    __tablename__ = "autorizacion"

    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitud.id"), nullable=False)
    etapa: Mapped[EtapaAutorizacion] = mapped_column(
        columna_enum(EtapaAutorizacion), nullable=False
    )
    responsable_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    estado: Mapped[EstadoAutorizacion] = mapped_column(
        columna_enum(EstadoAutorizacion), nullable=False, default=EstadoAutorizacion.PENDIENTE
    )
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[date] = mapped_column(nullable=False)

    solicitud: Mapped["Solicitud"] = relationship()  # noqa: F821
    responsable: Mapped["Usuario | None"] = relationship(  # noqa: F821
        foreign_keys=[responsable_id]
    )
    adjuntos: Mapped[list["AdjuntoAutorizacion"]] = relationship(
        back_populates="autorizacion", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Autorizacion solicitud={self.solicitud_id} etapa={self.etapa}>"


class AdjuntoAutorizacion(Base, AuditoriaMixin):
    __tablename__ = "adjunto_autorizacion"

    autorizacion_id: Mapped[int] = mapped_column(ForeignKey("autorizacion.id"), nullable=False)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documento.id"), nullable=False)

    autorizacion: Mapped["Autorizacion"] = relationship(back_populates="adjuntos")
    documento: Mapped["Documento"] = relationship()  # noqa: F821
