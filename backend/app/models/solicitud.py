"""§6.7 Solicitud: solicitudes del portal externo (nueva o ampliación), con tablas hijas."""
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import CoberturaGeografica, DirigidaA, EstadoSolicitud, TipoSolicitud
from app.models.mixins import AuditoriaMixin


class Solicitud(Base, AuditoriaMixin):
    __tablename__ = "solicitud"

    numero_referencia: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    tipo: Mapped[TipoSolicitud] = mapped_column(columna_enum(TipoSolicitud), nullable=False)
    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contrato.id"), nullable=True)
    unidad_negocio_id: Mapped[int] = mapped_column(
        ForeignKey("unidad_negocio.id"), nullable=False
    )
    dirigida_a: Mapped[DirigidaA] = mapped_column(columna_enum(DirigidaA), nullable=False)
    cobertura: Mapped[CoberturaGeografica] = mapped_column(
        columna_enum(CoberturaGeografica), nullable=False
    )
    provincias_involucradas: Mapped[str | None] = mapped_column(Text, nullable=True)
    postes_solicitados: Mapped[int] = mapped_column(default=0, nullable=False)
    ductos_solicitados_m: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    objetivo_proyecto: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_redes: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cronograma_inicio: Mapped[date | None] = mapped_column(nullable=True)
    cronograma_fin: Mapped[date | None] = mapped_column(nullable=True)
    puesta_en_servicio: Mapped[date | None] = mapped_column(nullable=True)
    estado: Mapped[EstadoSolicitud] = mapped_column(
        columna_enum(EstadoSolicitud), nullable=False, default=EstadoSolicitud.BORRADOR
    )
    fecha_creacion: Mapped[date] = mapped_column(nullable=False)

    cable_operadora: Mapped["CableOperadora"] = relationship()  # noqa: F821
    unidad_negocio: Mapped["UnidadNegocio"] = relationship()  # noqa: F821
    rutas_propuestas: Mapped[list["RutaPropuesta"]] = relationship(
        back_populates="solicitud", cascade="all, delete-orphan"
    )
    contactos: Mapped[list["ContactoSolicitud"]] = relationship(
        back_populates="solicitud", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Solicitud {self.numero_referencia}>"


class RutaPropuesta(Base, AuditoriaMixin):
    __tablename__ = "ruta_propuesta"

    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitud.id"), nullable=False)
    provincia: Mapped[str] = mapped_column(String(100), nullable=False)
    ciudad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recinto: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ruta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postes_usados: Mapped[int] = mapped_column(default=0, nullable=False)
    postes_nuevos: Mapped[int] = mapped_column(default=0, nullable=False)
    total_postes: Mapped[int] = mapped_column(default=0, nullable=False)

    solicitud: Mapped["Solicitud"] = relationship(back_populates="rutas_propuestas")


class ContactoSolicitud(Base, AuditoriaMixin):
    __tablename__ = "contacto_solicitud"

    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitud.id"), nullable=False)
    # Rol del contacto dentro de la solicitud (representante legal, responsable técnico,
    # coordinador de campo, contratista - §9.2).
    rol_contacto: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    solicitud: Mapped["Solicitud"] = relationship(back_populates="contactos")
