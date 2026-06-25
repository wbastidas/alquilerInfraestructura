"""Registro de auditoría (§4.7, §6.15): quién, qué, cuándo y desde dónde."""
from sqlalchemy.orm import Session

from app.models.enums import AccionAuditoria
from app.models.log_auditoria import LogAuditoria


def registrar_auditoria(
    db: Session,
    *,
    usuario_id: int | None,
    accion: AccionAuditoria,
    entidad_tipo: str,
    entidad_id: int | None = None,
    descripcion: str | None = None,
    valores_antes: dict | None = None,
    valores_despues: dict | None = None,
    ip_origen: str | None = None,
    user_agent: str | None = None,
) -> LogAuditoria:
    """Inserta una entrada inmutable de auditoría. No hace `commit`: se incluye en la
    misma transacción que la operación auditada para garantizar atomicidad."""
    entrada = LogAuditoria(
        usuario_id=usuario_id,
        accion=accion,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        descripcion=descripcion,
        valores_antes=valores_antes,
        valores_despues=valores_despues,
        ip_origen=ip_origen,
        user_agent=user_agent,
    )
    db.add(entrada)
    return entrada
