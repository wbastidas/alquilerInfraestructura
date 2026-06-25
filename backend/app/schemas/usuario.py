"""Esquemas de Usuario (§6.2)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import TipoCuenta


class UsuarioBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    nombre_completo: str
    correo: EmailStr
    rol_id: int
    unidad_negocio_id: int | None = None
    cable_operadora_id: int | None = None


class UsuarioCrear(UsuarioBase):
    tipo_cuenta: TipoCuenta
    # Requerido para LOCAL/PROVEEDOR; ignorado para AD (la clave la valida el dominio).
    password: str | None = Field(default=None, min_length=8, max_length=255)


class UsuarioActualizar(BaseModel):
    nombre_completo: str | None = None
    correo: EmailStr | None = None
    rol_id: int | None = None
    unidad_negocio_id: int | None = None
    activo: bool | None = None


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nombre_completo: str
    correo: str
    tipo_cuenta: TipoCuenta
    rol_id: int
    unidad_negocio_id: int | None
    cable_operadora_id: int | None
    activo: bool
    ultimo_acceso: datetime | None
