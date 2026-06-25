"""§6.12 CatalogoCanon: valores del canon anual por tipo de zona, versionables."""
from datetime import date
from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._helpers import columna_enum
from app.models.enums import TipoZona
from app.models.mixins import AuditoriaMixin


class CatalogoCanon(Base, AuditoriaMixin):
    __tablename__ = "catalogo_canon"

    tipo_zona: Mapped[TipoZona] = mapped_column(columna_enum(TipoZona), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    vigente_desde: Mapped[date] = mapped_column(nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(nullable=True)
    referencia_normativa: Mapped[str | None] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<CatalogoCanon {self.tipo_zona} {self.valor}>"
