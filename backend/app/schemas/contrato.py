"""Esquemas de Contrato (§6.5)."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import CoberturaGeografica, EstadoContrato


class ContratoBase(BaseModel):
    cable_operadora_id: int
    unidad_negocio_id: int
    numero_contrato: str
    tipo_cobertura: CoberturaGeografica
    fecha_suscripcion: date | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    poliza_numero: str | None = None
    poliza_aseguradora: str | None = None
    poliza_valor: Decimal | None = None
    poliza_vigencia_inicio: date | None = None
    poliza_vigencia_fin: date | None = None
    solicitud_id: int | None = None
    informe_factibilidad_id: int | None = None


class ContratoCrear(ContratoBase):
    pass


class ContratoActualizar(BaseModel):
    estado: EstadoContrato | None = None
    fecha_fin: date | None = None
    total_postes: int | None = None
    total_ductos_m: Decimal | None = None
    canon_anual_total: Decimal | None = None
    poliza_numero: str | None = None
    poliza_aseguradora: str | None = None
    poliza_valor: Decimal | None = None
    poliza_vigencia_inicio: date | None = None
    poliza_vigencia_fin: date | None = None


class ContratoRespuesta(ContratoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoContrato
    total_postes: int
    total_ductos_m: Decimal
    canon_anual_total: Decimal
