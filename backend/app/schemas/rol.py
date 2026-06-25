"""Esquemas de Rol (§6.3, §5.3)."""
from pydantic import BaseModel, ConfigDict


class RolRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    descripcion: str | None
