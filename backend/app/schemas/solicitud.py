"""Esquemas de Solicitud + RutaPropuesta + ContactoSolicitud (§6.7, §9.2, §9.4)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.enums import CoberturaGeografica, DirigidaA, EstadoSolicitud, TipoSolicitud


class RutaPropuestaBase(BaseModel):
    provincia: str
    ciudad: str | None = None
    recinto: str | None = None
    ruta: str | None = None
    postes_usados: int = 0
    postes_nuevos: int = 0
    total_postes: int = 0


class RutaPropuestaCrear(RutaPropuestaBase):
    pass


class RutaPropuestaRespuesta(RutaPropuestaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ContactoSolicitudBase(BaseModel):
    rol_contacto: str
    nombre: str
    telefono: str | None = None
    correo: str | None = None


class ContactoSolicitudCrear(ContactoSolicitudBase):
    pass


class ContactoSolicitudRespuesta(ContactoSolicitudBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SolicitudBase(BaseModel):
    cable_operadora_id: int
    contrato_id: int | None = None
    cobertura: CoberturaGeografica
    provincias_involucradas: str | None = None
    postes_solicitados: int = 0
    ductos_solicitados_m: Decimal = Decimal("0")
    objetivo_proyecto: str | None = None
    tipo_redes: str | None = None
    cronograma_inicio: date | None = None
    cronograma_fin: date | None = None
    puesta_en_servicio: date | None = None


class SolicitudCrear(SolicitudBase):
    tipo: TipoSolicitud
    rutas_propuestas: list[RutaPropuestaCrear] = []
    contactos: list[ContactoSolicitudCrear] = []

    @model_validator(mode="after")
    def _validar_contrato_segun_tipo(self) -> "SolicitudCrear":
        if self.tipo == TipoSolicitud.AMPLIACION and self.contrato_id is None:
            raise ValueError("Una solicitud de ampliación requiere indicar el contrato existente.")
        if self.tipo == TipoSolicitud.NUEVO_CONTRATO and self.contrato_id is not None:
            raise ValueError(
                "Una solicitud de nuevo contrato no debe referenciar un contrato existente."
            )
        return self


class SolicitudActualizar(BaseModel):
    """Edición permitida solo en BORRADOR/OBSERVADA (subsanación, §8)."""

    cobertura: CoberturaGeografica | None = None
    provincias_involucradas: str | None = None
    postes_solicitados: int | None = None
    ductos_solicitados_m: Decimal | None = None
    objetivo_proyecto: str | None = None
    tipo_redes: str | None = None
    cronograma_inicio: date | None = None
    cronograma_fin: date | None = None
    puesta_en_servicio: date | None = None
    rutas_propuestas: list[RutaPropuestaCrear] | None = None
    contactos: list[ContactoSolicitudCrear] | None = None


class SolicitudRespuesta(SolicitudBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_referencia: str
    tipo: TipoSolicitud
    unidad_negocio_id: int
    dirigida_a: DirigidaA
    estado: EstadoSolicitud
    fecha_creacion: date
    rutas_propuestas: list[RutaPropuestaRespuesta]
    contactos: list[ContactoSolicitudRespuesta]
