"""Esquemas de CableOperadora (§6.4) y sus tablas hijas."""
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import CoberturaGeografica, EstadoContratoOperadora


class TelefonoOperadoraBase(BaseModel):
    numero: str
    tipo: str | None = None


class TelefonoOperadoraRespuesta(TelefonoOperadoraBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class NombreComercialBase(BaseModel):
    nombre: str


class NombreComercialRespuesta(NombreComercialBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ResponsableTecnicoZonaBase(BaseModel):
    nombre: str
    cedula: str | None = None
    cargo: str | None = None
    telefono: str | None = None
    correo: str | None = None
    zona_cobertura: str | None = None


class ResponsableTecnicoZonaRespuesta(ResponsableTecnicoZonaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CableOperadoraBase(BaseModel):
    numero_registro: str
    nombre_empresa: str
    ruc: str | None = None
    cuenta_contrato: str | None = None
    representante_legal: str | None = None
    representante_cedula: str | None = None
    titulo_habilitante_numero: str | None = None
    titulo_habilitante_vigencia: date | None = None
    arcotel_resolucion: str | None = None
    servicios_autorizados: str | None = None
    cobertura_geografica: CoberturaGeografica
    correo: str | None = None
    tipo_contrato: CoberturaGeografica
    unidad_negocio_id: int


class CableOperadoraCrear(CableOperadoraBase):
    nombres_comerciales: list[NombreComercialBase] = []
    telefonos: list[TelefonoOperadoraBase] = []
    responsables_tecnicos: list[ResponsableTecnicoZonaBase] = []


class CableOperadoraActualizar(BaseModel):
    nombre_empresa: str | None = None
    ruc: str | None = None
    representante_legal: str | None = None
    representante_cedula: str | None = None
    estado_contrato: EstadoContratoOperadora | None = None
    fecha_firma_contrato: date | None = None
    fecha_caducidad: date | None = None
    correo: str | None = None


class CableOperadoraRespuesta(CableOperadoraBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado_contrato: EstadoContratoOperadora
    fecha_firma_contrato: date | None
    fecha_caducidad: date | None
    nombres_comerciales: list[NombreComercialRespuesta] = []
    telefonos: list[TelefonoOperadoraRespuesta] = []
    responsables_tecnicos: list[ResponsableTecnicoZonaRespuesta] = []
