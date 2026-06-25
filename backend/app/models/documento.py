"""§6.8 Documento: archivos cargados/generados, con validaciones de seguridad (§4.8)."""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import EntidadTipoDocumento, EstadoValidacionDocumento, TipoDocumento
from app.models.mixins import AuditoriaMixin


class Documento(Base, AuditoriaMixin):
    __tablename__ = "documento"

    entidad_tipo: Mapped[EntidadTipoDocumento] = mapped_column(
        columna_enum(EntidadTipoDocumento), nullable=False
    )
    entidad_id: Mapped[int] = mapped_column(nullable=False, index=True)
    tipo_documento: Mapped[TipoDocumento] = mapped_column(
        columna_enum(TipoDocumento, longitud=50), nullable=False
    )
    nombre_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_almacenamiento: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    estado_validacion: Mapped[EstadoValidacionDocumento] = mapped_column(
        columna_enum(EstadoValidacionDocumento),
        nullable=False,
        default=EstadoValidacionDocumento.PENDIENTE,
    )
    observacion_validacion: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Documento {self.nombre_archivo}>"
