"""Esquemas de Alerta (§6.14): vencimientos de contrato, póliza, título
habilitante y morosidad."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SeveridadAlerta, TipoAlerta


class AlertaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoAlerta
    entidad_tipo: str
    entidad_id: int
    unidad_negocio_id: int | None
    mensaje: str
    severidad: SeveridadAlerta
    fecha_generacion: datetime
    leida: bool
