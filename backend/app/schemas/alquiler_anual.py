"""Esquemas de AlquilerAnual + PostePorZona (§6.6)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstadoPago, TipoZona


class PostePorZonaBase(BaseModel):
    provincia: str
    canton: str
    parroquia: str | None = None
    tipo_zona: TipoZona
    cantidad_postes: int = 0
    cantidad_ductos_m: Decimal = Decimal("0")


class PostePorZonaCrear(PostePorZonaBase):
    pass


class PostePorZonaRespuesta(PostePorZonaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canon_unitario: Decimal
    subtotal: Decimal


class AlquilerAnualBase(BaseModel):
    cable_operadora_id: int
    contrato_id: int | None = None
    unidad_negocio_id: int
    anio: int
    postes_sig: int = 0
    postes_fisicos: int = 0
    fecha_facturacion: date | None = None
    observaciones: str | None = None
    poliza_garantia_fecha: date | None = None
    poliza_garantia_archivo_id: int | None = None


class AlquilerAnualCrear(AlquilerAnualBase):
    postes_por_zona: list[PostePorZonaCrear] = []


class AlquilerAnualActualizar(BaseModel):
    postes_sig: int | None = None
    postes_fisicos: int | None = None
    monto_recaudado: Decimal | None = None
    fecha_facturacion: date | None = None
    observaciones: str | None = None
    poliza_garantia_fecha: date | None = None
    poliza_garantia_archivo_id: int | None = None
    # Si se envía, reemplaza por completo el desglose de zonas y recalcula el canon.
    postes_por_zona: list[PostePorZonaCrear] | None = None


class AlquilerAnualRespuesta(AlquilerAnualBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monto_facturado: Decimal
    monto_recaudado: Decimal
    monto_pendiente_recaudar: Decimal
    estado_pago: EstadoPago
    postes_por_zona: list[PostePorZonaRespuesta]
