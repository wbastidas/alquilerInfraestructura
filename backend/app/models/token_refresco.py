"""Tabla de soporte para revocación/rotación de refresh tokens (§4.1).

No es una entidad de negocio del §6, sino infraestructura de seguridad: permite
mantener una "lista negra" persistente de refresh tokens emitidos, requerida
por la especificación para poder revocarlos (logout, rotación, compromiso de
credenciales) sin depender únicamente de su expiración natural.
"""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import AuditoriaMixin


class TokenRefrescoRevocado(Base, AuditoriaMixin):
    __tablename__ = "token_refresco_revocado"

    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    expira_en: Mapped[datetime] = mapped_column(nullable=False)
    revocado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])  # noqa: F821
