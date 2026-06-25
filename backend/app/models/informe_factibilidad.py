"""§6.9 InformeFactibilidad: informe técnico generado en la etapa REVISION_TECNICA."""
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import CoberturaGeografica
from app.models.mixins import AuditoriaMixin


class InformeFactibilidad(Base, AuditoriaMixin):
    __tablename__ = "informe_factibilidad"

    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitud.id"), nullable=False)
    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    unidad_negocio_id: Mapped[int] = mapped_column(
        ForeignKey("unidad_negocio.id"), nullable=False
    )
    codigo_oficio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha: Mapped[date] = mapped_column(nullable=False)
    cobertura: Mapped[CoberturaGeografica] = mapped_column(
        columna_enum(CoberturaGeografica), nullable=False
    )
    postes_solicitados: Mapped[int] = mapped_column(default=0, nullable=False)
    postes_viables: Mapped[int] = mapped_column(default=0, nullable=False)
    postes_no_viables: Mapped[int] = mapped_column(default=0, nullable=False)
    ductos_solicitados_m: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    ductos_viables_m: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    ductos_no_viables_m: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    porcentaje_factibilidad: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )
    revision_documental_estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_ultima_subsanacion: Mapped[date | None] = mapped_column(nullable=True)
    sig_validado: Mapped[bool] = mapped_column(default=False, nullable=False)
    sig_validador: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sig_fecha_validacion: Mapped[date | None] = mapped_column(nullable=True)
    inspeccion_fecha_inicio: Mapped[date | None] = mapped_column(nullable=True)
    inspeccion_fecha_fin: Mapped[date | None] = mapped_column(nullable=True)
    rutas_verificadas: Mapped[str | None] = mapped_column(Text, nullable=True)
    personal_participante: Mapped[str | None] = mapped_column(Text, nullable=True)
    conclusiones: Mapped[str | None] = mapped_column(Text, nullable=True)
    archivo_id: Mapped[int | None] = mapped_column(ForeignKey("documento.id"), nullable=True)

    solicitud: Mapped["Solicitud"] = relationship()  # noqa: F821
    cable_operadora: Mapped["CableOperadora"] = relationship()  # noqa: F821
    unidad_negocio: Mapped["UnidadNegocio"] = relationship()  # noqa: F821
    archivo: Mapped["Documento | None"] = relationship()  # noqa: F821
    ubicaciones: Mapped[list["UbicacionInformeFactibilidad"]] = relationship(
        back_populates="informe_factibilidad", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InformeFactibilidad solicitud={self.solicitud_id}>"


class UbicacionInformeFactibilidad(Base, AuditoriaMixin):
    """Tabla hija `ubicaciones`: provincia, cantones, UN involucrada."""

    __tablename__ = "ubicacion_informe_factibilidad"

    informe_factibilidad_id: Mapped[int] = mapped_column(
        ForeignKey("informe_factibilidad.id"), nullable=False
    )
    provincia: Mapped[str] = mapped_column(String(100), nullable=False)
    cantones: Mapped[str | None] = mapped_column(Text, nullable=True)
    unidad_negocio_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidad_negocio.id"), nullable=True
    )

    informe_factibilidad: Mapped["InformeFactibilidad"] = relationship(
        back_populates="ubicaciones"
    )
