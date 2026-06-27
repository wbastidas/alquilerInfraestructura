"""Esquemas de Factura y Pago (§6.11)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstadoFactura, MetodoPago, TipoPago


class FacturaBase(BaseModel):
    cable_operadora_id: int
    contrato_id: int
    alquiler_anual_id: int
    numero_factura: str
    fecha_emision: date
    fecha_vencimiento: date
    monto: Decimal
    iva: Decimal = Decimal("0")
    archivo_xml_id: int | None = None
    archivo_pdf_id: int | None = None


class FacturaCrear(FacturaBase):
    pass


class FacturaRespuesta(FacturaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total: Decimal
    estado: EstadoFactura


class PagoBase(BaseModel):
    factura_id: int
    monto: Decimal
    tipo: TipoPago
    metodo: MetodoPago
    referencia_transaccion: str | None = None
    fecha_pago: date


class PagoCrear(PagoBase):
    pass


class PagoRespuesta(PagoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cable_operadora_id: int
    conciliado: bool
    fecha_conciliacion: date | None = None


class ReporteMorosidadItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    factura_id: int
    numero_factura: str
    cable_operadora_id: int
    fecha_vencimiento: date
    dias_mora: int
    saldo_pendiente: Decimal
    interes_mora: Decimal
