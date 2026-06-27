"""Esquemas de Novedad y FotografiaNovedad (§6.13, §7.6)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstadoNovedad, TipoNovedad


class NovedadBase(BaseModel):
    cable_operadora_id: int
    contrato_id: int | None = None
    unidad_negocio_id: int
    tipo: TipoNovedad
    descripcion: str | None = None
    fecha_programada: date | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None


class NovedadCrear(NovedadBase):
    pass


class NovedadActualizar(BaseModel):
    estado: EstadoNovedad | None = None
    descripcion: str | None = None
    fecha_ejecucion: date | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None


class FotografiaNovedadRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    novedad_id: int
    documento_id: int
    latitud: Decimal | None
    longitud: Decimal | None


class NovedadRespuesta(NovedadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoNovedad
    fecha_ejecucion: date | None
    ficha_informe_id: int | None
    fotografias: list[FotografiaNovedadRespuesta] = []
