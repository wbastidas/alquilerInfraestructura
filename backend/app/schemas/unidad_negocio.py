"""Esquemas de UnidadNegocio (§6.1)."""
from pydantic import BaseModel, ConfigDict


class UnidadNegocioBase(BaseModel):
    codigo: str
    nombre: str
    provincia: str
    activo: bool = True


class UnidadNegocioCrear(UnidadNegocioBase):
    pass


class UnidadNegocioActualizar(BaseModel):
    nombre: str | None = None
    provincia: str | None = None
    activo: bool | None = None


class UnidadNegocioRespuesta(UnidadNegocioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
