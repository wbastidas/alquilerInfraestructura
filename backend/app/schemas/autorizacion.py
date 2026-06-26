"""Esquemas de Autorizacion: decisión y consulta del paso de workflow (§6.10, §7.5, §8)."""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import EstadoAutorizacion, EtapaAutorizacion

_DECISIONES_VALIDAS = {
    EstadoAutorizacion.APROBADO,
    EstadoAutorizacion.RECHAZADO,
    EstadoAutorizacion.OBSERVADO,
}


class AutorizacionDecision(BaseModel):
    estado: EstadoAutorizacion
    comentario: str | None = None

    @field_validator("estado")
    @classmethod
    def _validar_decision(cls, valor: EstadoAutorizacion) -> EstadoAutorizacion:
        if valor not in _DECISIONES_VALIDAS:
            raise ValueError("La decisión debe ser APROBADO, RECHAZADO u OBSERVADO.")
        return valor


class AutorizacionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    etapa: EtapaAutorizacion
    responsable_id: int | None
    estado: EstadoAutorizacion
    comentario: str | None
    fecha: date
