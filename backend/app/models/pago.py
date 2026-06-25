"""§6.11 Factura / Pago: gestión de facturación y recaudación."""
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, ValorCifrado
from app.models._helpers import columna_enum
from app.models.enums import EstadoFactura, MetodoPago, TipoPago
from app.models.mixins import AuditoriaMixin


class Factura(Base, AuditoriaMixin):
    __tablename__ = "factura"

    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    contrato_id: Mapped[int] = mapped_column(ForeignKey("contrato.id"), nullable=False)
    alquiler_anual_id: Mapped[int] = mapped_column(
        ForeignKey("alquiler_anual.id"), nullable=False
    )
    numero_factura: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    fecha_emision: Mapped[date] = mapped_column(nullable=False)
    # Vencimiento de factura a 30 días (cláusula del modelo base, §9.1). TODO: confirmar con
    # cliente si el plazo es configurable por tipo de cliente/contrato.
    fecha_vencimiento: Mapped[date] = mapped_column(nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    estado: Mapped[EstadoFactura] = mapped_column(
        columna_enum(EstadoFactura), nullable=False, default=EstadoFactura.EMITIDA
    )
    archivo_xml_id: Mapped[int | None] = mapped_column(ForeignKey("documento.id"), nullable=True)
    archivo_pdf_id: Mapped[int | None] = mapped_column(ForeignKey("documento.id"), nullable=True)

    cable_operadora: Mapped["CableOperadora"] = relationship()  # noqa: F821
    contrato: Mapped["Contrato"] = relationship()  # noqa: F821
    alquiler_anual: Mapped["AlquilerAnual"] = relationship()  # noqa: F821
    pagos: Mapped[list["Pago"]] = relationship(back_populates="factura")

    def __repr__(self) -> str:
        return f"<Factura {self.numero_factura}>"


class Pago(Base, AuditoriaMixin):
    __tablename__ = "pago"

    factura_id: Mapped[int] = mapped_column(ForeignKey("factura.id"), nullable=False)
    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tipo: Mapped[TipoPago] = mapped_column(columna_enum(TipoPago), nullable=False)
    metodo: Mapped[MetodoPago] = mapped_column(columna_enum(MetodoPago), nullable=False)
    referencia_transaccion: Mapped[str | None] = mapped_column(ValorCifrado(100), nullable=True)
    fecha_pago: Mapped[date] = mapped_column(nullable=False)
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_conciliacion: Mapped[date | None] = mapped_column(nullable=True)

    factura: Mapped["Factura"] = relationship(back_populates="pagos")
    cable_operadora: Mapped["CableOperadora"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Pago factura={self.factura_id} monto={self.monto}>"
