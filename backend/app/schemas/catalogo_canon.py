"""Esquemas de CatalogoCanon (§6.12)."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoZona


class CatalogoCanonBase(BaseModel):
    tipo_zona: TipoZona
    valor: Decimal
    vigente_desde: date
    vigente_hasta: date | None = None
    referencia_normativa: str | None = None


class CatalogoCanonCrear(CatalogoCanonBase):
    pass


class CatalogoCanonRespuesta(CatalogoCanonBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
