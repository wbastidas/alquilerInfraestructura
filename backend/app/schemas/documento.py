"""Esquemas de Documento (§6.8, §11): carga, validación de checklist y descarga (§4.8)."""

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import EstadoValidacionDocumento, TipoDocumento

_DECISIONES_VALIDAS = {
    EstadoValidacionDocumento.VALIDADO,
    EstadoValidacionDocumento.OBSERVADO,
    EstadoValidacionDocumento.RECHAZADO,
}


class DocumentoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entidad_id: int
    tipo_documento: TipoDocumento
    nombre_archivo: str
    mime_type: str
    tamano_bytes: int
    hash_sha256: str
    estado_validacion: EstadoValidacionDocumento
    observacion_validacion: str | None


class DocumentoValidar(BaseModel):
    estado_validacion: EstadoValidacionDocumento
    observacion_validacion: str | None = None

    @field_validator("estado_validacion")
    @classmethod
    def _validar_decision(cls, valor: EstadoValidacionDocumento) -> EstadoValidacionDocumento:
        if valor not in _DECISIONES_VALIDAS:
            raise ValueError("El estado debe ser VALIDADO, OBSERVADO o RECHAZADO.")
        return valor


class ChecklistItemRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo_documento: TipoDocumento
    documento_id: int | None
    estado_validacion: EstadoValidacionDocumento
    observacion_validacion: str | None
