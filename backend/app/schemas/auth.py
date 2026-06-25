"""Esquemas Pydantic para autenticación (§5)."""
from pydantic import BaseModel, Field


class LoginLocalRequest(BaseModel):
    """Login con usuario/clave local (proveedores y cuentas de respaldo, §5.1)."""

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class LoginDominioRequest(BaseModel):
    """Login contra dominio Windows / Active Directory vía LDAP (§5.1)."""

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UsuarioActual(BaseModel):
    id: int
    username: str
    nombre_completo: str
    rol: str
    unidad_negocio_id: int | None
    cable_operadora_id: int | None
    tipo_cuenta: str

    model_config = {"from_attributes": True}
