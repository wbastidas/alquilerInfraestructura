"""§6.4 CableOperadora: empresa proveedora/arrendataria, con tablas hijas."""

from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, ValorCifrado
from app.models._helpers import columna_enum
from app.models.enums import CoberturaGeografica, EstadoContratoOperadora
from app.models.mixins import AuditoriaMixin


class CableOperadora(Base, AuditoriaMixin):
    __tablename__ = "cable_operadora"

    numero_registro: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    nombre_empresa: Mapped[str] = mapped_column(String(250), nullable=False)
    ruc: Mapped[str | None] = mapped_column(ValorCifrado(20), nullable=True)
    cuenta_contrato: Mapped[str | None] = mapped_column(String(50), nullable=True)
    representante_legal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    representante_cedula: Mapped[str | None] = mapped_column(ValorCifrado(20), nullable=True)
    titulo_habilitante_numero: Mapped[str | None] = mapped_column(String(100), nullable=True)
    titulo_habilitante_vigencia: Mapped[date | None] = mapped_column(nullable=True)
    arcotel_resolucion: Mapped[str | None] = mapped_column(String(150), nullable=True)
    servicios_autorizados: Mapped[str | None] = mapped_column(Text, nullable=True)
    cobertura_geografica: Mapped[CoberturaGeografica] = mapped_column(
        columna_enum(CoberturaGeografica), nullable=False
    )
    correo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado_contrato: Mapped[EstadoContratoOperadora] = mapped_column(
        columna_enum(EstadoContratoOperadora),
        nullable=False,
        default=EstadoContratoOperadora.EN_JURIDICO,
    )
    fecha_firma_contrato: Mapped[date | None] = mapped_column(nullable=True)
    fecha_caducidad: Mapped[date | None] = mapped_column(nullable=True)
    # TODO: confirmar con cliente si "administrador_contrato" debe ser FK a Usuario o texto libre;
    # se modela como FK opcional + texto libre de respaldo para no perder información.
    # use_alter=True rompe el ciclo de FKs cable_operadora<->usuario (un Usuario PROVEEDOR
    # referencia su cable_operadora, y esta referencia opcionalmente a su administrador).
    administrador_contrato_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", use_alter=True, name="fk_cable_operadora_administrador_contrato"),
        nullable=True,
    )
    administrador_contrato_texto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo_contrato: Mapped[CoberturaGeografica] = mapped_column(
        columna_enum(CoberturaGeografica), nullable=False
    )
    unidad_negocio_id: Mapped[int] = mapped_column(ForeignKey("unidad_negocio.id"), nullable=False)

    unidad_negocio: Mapped["UnidadNegocio"] = relationship()  # noqa: F821
    administrador_contrato: Mapped["Usuario | None"] = relationship(  # noqa: F821
        foreign_keys=[administrador_contrato_id]
    )
    nombres_comerciales: Mapped[list["NombreComercial"]] = relationship(
        back_populates="cable_operadora", cascade="all, delete-orphan"
    )
    telefonos: Mapped[list["TelefonoOperadora"]] = relationship(
        back_populates="cable_operadora", cascade="all, delete-orphan"
    )
    responsables_tecnicos: Mapped[list["ResponsableTecnicoZona"]] = relationship(
        back_populates="cable_operadora", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CableOperadora {self.numero_registro} {self.nombre_empresa}>"


class NombreComercial(Base, AuditoriaMixin):
    __tablename__ = "nombre_comercial"

    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)

    cable_operadora: Mapped["CableOperadora"] = relationship(back_populates="nombres_comerciales")


class TelefonoOperadora(Base, AuditoriaMixin):
    __tablename__ = "telefono_operadora"

    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)

    cable_operadora: Mapped["CableOperadora"] = relationship(back_populates="telefonos")


class ResponsableTecnicoZona(Base, AuditoriaMixin):
    __tablename__ = "responsable_tecnico_zona"

    cable_operadora_id: Mapped[int] = mapped_column(
        ForeignKey("cable_operadora.id"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    cedula: Mapped[str | None] = mapped_column(ValorCifrado(20), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    zona_cobertura: Mapped[str | None] = mapped_column(String(200), nullable=True)

    cable_operadora: Mapped["CableOperadora"] = relationship(back_populates="responsables_tecnicos")
