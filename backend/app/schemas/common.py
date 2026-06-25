"""Esquemas comunes: paginación y envoltura de listados (§10)."""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ParametrosPaginacion(BaseModel):
    pagina: int = 1
    tamano_pagina: int = 20

    @property
    def offset(self) -> int:
        return (self.pagina - 1) * self.tamano_pagina


class RespuestaPaginada(BaseModel, Generic[T]):
    total: int
    pagina: int
    tamano_pagina: int
    items: list[T]
