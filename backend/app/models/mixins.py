"""Mixins comunes a todas las entidades del modelo de datos (§6)."""
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class AuditoriaMixin:
    """Toda entidad incluye id, marcas de tiempo y autoría de creación/edición."""

    id: Mapped[int] = mapped_column(primary_key=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @declared_attr
    def creado_por(cls) -> Mapped[int | None]:  # noqa: N805
        return mapped_column(
            ForeignKey(
                "usuario.id", use_alter=True, name=f"fk_{cls.__tablename__}_creado_por_usuario"
            ),
            nullable=True,
        )

    @declared_attr
    def actualizado_por(cls) -> Mapped[int | None]:  # noqa: N805
        return mapped_column(
            ForeignKey(
                "usuario.id",
                use_alter=True,
                name=f"fk_{cls.__tablename__}_actualizado_por_usuario",
            ),
            nullable=True,
        )
