"""§6.6 AlquilerAnual + PostePorZona: control anual de postes y recaudación."""
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import EstadoPago, TipoZona
from app.models.mixins import AuditoriaMixin


class AlquilerAnual(Base, AuditoriaMixin):
    __tablename__ = "alquiler_anual"
    __table_args__ = (
        UniqueConstraint("cable_operadora_id", "anio", name="uq_alquiler_anual_operadora_anio"),
    )

    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contrato.id"), nullable=True)
    unidad_negocio_id: Mapped[int] = mapped_column(
        ForeignKey("unidad_negocio.id"), nullable=False
    )
    anio: Mapped[int] = mapped_column(nullable=False, index=True)
    postes_sig: Mapped[int] = mapped_column(default=0, nullable=False)
    postes_fisicos: Mapped[int] = mapped_column(default=0, nullable=False)
    monto_facturado: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    monto_recaudado: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    # Derivado: facturado - recaudado. Se recalcula en el servicio, no es generated column,
    # para mantener portabilidad SQLite/MariaDB en pruebas y producción.
    monto_pendiente_recaudar: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    fecha_facturacion: Mapped[date | None] = mapped_column(nullable=True)
    estado_pago: Mapped[EstadoPago] = mapped_column(
        columna_enum(EstadoPago), nullable=False, default=EstadoPago.PENDIENTE
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    poliza_garantia_fecha: Mapped[date | None] = mapped_column(nullable=True)
    poliza_garantia_archivo_id: Mapped[int | None] = mapped_column(
        ForeignKey("documento.id"), nullable=True
    )

    cable_operadora: Mapped["CableOperadora"] = relationship()  # noqa: F821
    contrato: Mapped["Contrato | None"] = relationship()  # noqa: F821
    unidad_negocio: Mapped["UnidadNegocio"] = relationship()  # noqa: F821
    postes_por_zona: Mapped[list["PostePorZona"]] = relationship(
        back_populates="alquiler_anual", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AlquilerAnual operadora={self.cable_operadora_id} anio={self.anio}>"


class PostePorZona(Base, AuditoriaMixin):
    __tablename__ = "poste_por_zona"

    alquiler_anual_id: Mapped[int] = mapped_column(
        ForeignKey("alquiler_anual.id"), nullable=False
    )
    provincia: Mapped[str] = mapped_column(String(100), nullable=False)
    canton: Mapped[str] = mapped_column(String(100), nullable=False)
    parroquia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tipo_zona: Mapped[TipoZona] = mapped_column(columna_enum(TipoZona), nullable=False)
    cantidad_postes: Mapped[int] = mapped_column(default=0, nullable=False)
    cantidad_ductos_m: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    canon_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # Derivado: cantidad_postes * canon_unitario, recalculado en el servicio (§7.2).
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )

    alquiler_anual: Mapped["AlquilerAnual"] = relationship(back_populates="postes_por_zona")
