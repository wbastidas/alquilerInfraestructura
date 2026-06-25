"""§6.13 Novedad: inspecciones, daños y mantenimientos registrados en campo."""
from datetime import date

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import EstadoNovedad, TipoNovedad
from app.models.mixins import AuditoriaMixin


class Novedad(Base, AuditoriaMixin):
    __tablename__ = "novedad"

    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contrato.id"), nullable=True)
    unidad_negocio_id: Mapped[int] = mapped_column(
        ForeignKey("unidad_negocio.id"), nullable=False
    )
    tipo: Mapped[TipoNovedad] = mapped_column(columna_enum(TipoNovedad), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_programada: Mapped[date | None] = mapped_column(nullable=True)
    fecha_ejecucion: Mapped[date | None] = mapped_column(nullable=True)
    estado: Mapped[EstadoNovedad] = mapped_column(
        columna_enum(EstadoNovedad), nullable=False, default=EstadoNovedad.PROGRAMADA
    )
    latitud: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitud: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    ficha_informe_id: Mapped[int | None] = mapped_column(
        ForeignKey("documento.id"), nullable=True
    )

    cable_operadora: Mapped["CableOperadora"] = relationship()  # noqa: F821
    contrato: Mapped["Contrato | None"] = relationship()  # noqa: F821
    unidad_negocio: Mapped["UnidadNegocio"] = relationship()  # noqa: F821
    ficha_informe: Mapped["Documento | None"] = relationship()  # noqa: F821
    fotografias: Mapped[list["FotografiaNovedad"]] = relationship(
        back_populates="novedad", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Novedad {self.tipo} operadora={self.cable_operadora_id}>"


class FotografiaNovedad(Base, AuditoriaMixin):
    __tablename__ = "fotografia_novedad"

    novedad_id: Mapped[int] = mapped_column(ForeignKey("novedad.id"), nullable=False)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documento.id"), nullable=False)
    latitud: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitud: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    novedad: Mapped["Novedad"] = relationship(back_populates="fotografias")
    documento: Mapped["Documento"] = relationship()  # noqa: F821
