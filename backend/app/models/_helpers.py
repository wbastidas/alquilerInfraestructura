"""Utilidades compartidas entre modelos."""
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E")


def columna_enum(tipo_enum: type[E], longitud: int = 40) -> SAEnum:
    """Crea un tipo Enum de SQLAlchemy almacenado como VARCHAR (no ENUM nativo),
    para mantener portabilidad entre MariaDB (producción) y SQLite (pruebas)."""
    return SAEnum(
        tipo_enum,
        native_enum=False,
        length=longitud,
        values_callable=lambda enum_cls: [miembro.value for miembro in enum_cls],
    )
