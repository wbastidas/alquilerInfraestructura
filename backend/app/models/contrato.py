"""§6.5 Contrato: producto del flujo de autorización para una CableOperadora."""

from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import CoberturaGeografica, EstadoContrato
from app.models.mixins import AuditoriaMixin


class Contrato(Base, AuditoriaMixin):
    __tablename__ = "contrato"

    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    unidad_negocio_id: Mapped[int] = mapped_column(ForeignKey("unidad_negocio.id"), nullable=False)
    numero_contrato: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tipo_cobertura: Mapped[CoberturaGeografica] = mapped_column(
        columna_enum(CoberturaGeografica), nullable=False
    )
    fecha_suscripcion: Mapped[date | None] = mapped_column(nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(nullable=True)
    # Vigencia 2 años, renovable una vez (cláusula 8 del modelo). TODO: confirmar con cliente
    # si el sistema debe calcular fecha_fin automáticamente o se ingresa manualmente.
    fecha_fin: Mapped[date | None] = mapped_column(nullable=True)
    estado: Mapped[EstadoContrato] = mapped_column(
        columna_enum(EstadoContrato), nullable=False, default=EstadoContrato.EN_JURIDICO
    )
    total_postes: Mapped[int] = mapped_column(default=0, nullable=False)
    total_ductos_m: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    canon_anual_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    poliza_numero: Mapped[str | None] = mapped_column(String(100), nullable=True)
    poliza_aseguradora: Mapped[str | None] = mapped_column(String(200), nullable=True)
    poliza_valor: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    poliza_vigencia_inicio: Mapped[date | None] = mapped_column(nullable=True)
    poliza_vigencia_fin: Mapped[date | None] = mapped_column(nullable=True)
    archivo_contrato_id: Mapped[int | None] = mapped_column(
        ForeignKey("documento.id"), nullable=True
    )
    # use_alter=True rompe los ciclos de FKs contrato<->solicitud<->informe_factibilidad
    # (una Solicitud referencia opcionalmente el Contrato que produjo, y un Contrato
    # referencia opcionalmente la Solicitud/Informe que lo originaron).
    solicitud_id: Mapped[int | None] = mapped_column(
        ForeignKey("solicitud.id", use_alter=True, name="fk_contrato_solicitud"), nullable=True
    )
    informe_factibilidad_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "informe_factibilidad.id", use_alter=True, name="fk_contrato_informe_factibilidad"
        ),
        nullable=True,
    )

    cable_operadora: Mapped["CableOperadora"] = relationship()  # noqa: F821
    unidad_negocio: Mapped["UnidadNegocio"] = relationship()  # noqa: F821
    archivo_contrato: Mapped["Documento | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Contrato {self.numero_contrato}>"
