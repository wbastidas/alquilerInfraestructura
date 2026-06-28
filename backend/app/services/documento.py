"""Servicio de Documento (§4.8, §6.8, §11): carga validada, descarga auditada (la auditoría en
sí la registra el router, vía `app.auditoria.servicio`) y checklist documental del proveedor.

Validación de subida (§4.8): tipo MIME + extensión contra una lista blanca, tamaño máximo
configurable, nombre de archivo saneado y almacenamiento fuera del webroot (directorio
`almacenamiento_documentos_dir`, fuera de `app/`).
"""

import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto
from app.core.checklist import TIPOS_CHECKLIST_SOLICITUD
from app.core.config import obtener_configuracion
from app.core.exceptions import PermisoDenegado, RecursoNoEncontrado
from app.models.documento import Documento
from app.models.enums import EntidadTipoDocumento, EstadoValidacionDocumento, TipoDocumento
from app.schemas.documento import DocumentoValidar
from app.services import solicitud as solicitud_servicio

_EXTENSIONES_PERMITIDAS: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".zip": {"application/zip", "application/x-zip-compressed", "application/octet-stream"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
}


@dataclass
class ChecklistItem:
    tipo_documento: TipoDocumento
    documento_id: int | None
    estado_validacion: EstadoValidacionDocumento
    observacion_validacion: str | None


def _sanitizar_nombre(nombre: str) -> str:
    nombre = Path(nombre).name  # descarta cualquier componente de ruta (path traversal)
    nombre = re.sub(r"[^A-Za-z0-9._-]", "_", nombre)
    return nombre[-150:] or "archivo"


def _validar_archivo(nombre_archivo: str, mime_type: str, tamano_bytes: int) -> None:
    extension = Path(nombre_archivo).suffix.lower()
    mimes_validos = _EXTENSIONES_PERMITIDAS.get(extension)
    if mimes_validos is None:
        raise ValueError(f"Extensión de archivo no permitida: {extension or '(sin extensión)'}.")
    if mime_type not in mimes_validos:
        raise ValueError(f"Tipo MIME no permitido para {extension}: {mime_type}.")
    if tamano_bytes == 0:
        raise ValueError("El archivo está vacío.")
    config = obtener_configuracion()
    limite_bytes = config.tamano_maximo_archivo_mb * 1024 * 1024
    if tamano_bytes > limite_bytes:
        raise ValueError(
            f"El archivo excede el tamaño máximo permitido ({config.tamano_maximo_archivo_mb} MB)."
        )


def subir_para_solicitud(
    db: Session,
    solicitud_id: int,
    tipo_documento: TipoDocumento,
    archivo: UploadFile,
    contenido: bytes,
    usuario_actual: UsuarioContexto,
) -> Documento:
    """Carga un documento del checklist (§11) asociado a una Solicitud."""
    solicitud_servicio.obtener(db, solicitud_id, usuario_actual)  # valida acceso y existencia
    nombre_saneado = _sanitizar_nombre(archivo.filename or "archivo")
    _validar_archivo(nombre_saneado, archivo.content_type or "", len(contenido))

    config = obtener_configuracion()
    directorio = Path(config.almacenamiento_documentos_dir) / "solicitud" / str(solicitud_id)
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / f"{uuid.uuid4().hex}_{nombre_saneado}"
    ruta.write_bytes(contenido)

    documento = Documento(
        entidad_tipo=EntidadTipoDocumento.SOLICITUD,
        entidad_id=solicitud_id,
        tipo_documento=tipo_documento,
        nombre_archivo=nombre_saneado,
        ruta_almacenamiento=str(ruta),
        mime_type=archivo.content_type or "application/octet-stream",
        tamano_bytes=len(contenido),
        hash_sha256=hashlib.sha256(contenido).hexdigest(),
        estado_validacion=EstadoValidacionDocumento.PENDIENTE,
        creado_por=usuario_actual.id,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


def listar_por_solicitud(
    db: Session, solicitud_id: int, usuario_actual: UsuarioContexto
) -> list[Documento]:
    solicitud_servicio.obtener(db, solicitud_id, usuario_actual)  # valida acceso y existencia
    query = (
        select(Documento)
        .where(
            Documento.entidad_tipo == EntidadTipoDocumento.SOLICITUD,
            Documento.entidad_id == solicitud_id,
        )
        .order_by(Documento.id)
    )
    return list(db.scalars(query))


def obtener(db: Session, documento_id: int, usuario_actual: UsuarioContexto) -> Documento:
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise RecursoNoEncontrado("Documento no encontrado.")
    if documento.entidad_tipo == EntidadTipoDocumento.SOLICITUD:
        solicitud_servicio.obtener(db, documento.entidad_id, usuario_actual)
    elif not usuario_actual.es_matriz_o_superadmin:
        raise PermisoDenegado("No tiene acceso a este documento.")
    return documento


def descargar(
    db: Session, documento_id: int, usuario_actual: UsuarioContexto
) -> tuple[Documento, bytes]:
    documento = obtener(db, documento_id, usuario_actual)
    contenido = Path(documento.ruta_almacenamiento).read_bytes()
    return documento, contenido


def validar(
    db: Session, documento_id: int, datos: DocumentoValidar, usuario_actual: UsuarioContexto
) -> Documento:
    """El personal interno (UN/Matriz) valida/observa/rechaza un documento del checklist (§11)."""
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no puede validar sus propios documentos.")
    documento = obtener(db, documento_id, usuario_actual)
    documento.estado_validacion = datos.estado_validacion
    documento.observacion_validacion = datos.observacion_validacion
    db.commit()
    db.refresh(documento)
    return documento


def obtener_checklist(
    db: Session, solicitud_id: int, usuario_actual: UsuarioContexto
) -> list[ChecklistItem]:
    documentos = listar_por_solicitud(db, solicitud_id, usuario_actual)
    ultimo_por_tipo: dict[TipoDocumento, Documento] = {}
    for documento in documentos:
        ultimo_por_tipo[documento.tipo_documento] = documento  # ya viene ordenado por id

    return [
        ChecklistItem(
            tipo_documento=tipo,
            documento_id=ultimo_por_tipo[tipo].id if tipo in ultimo_por_tipo else None,
            estado_validacion=(
                ultimo_por_tipo[tipo].estado_validacion
                if tipo in ultimo_por_tipo
                else EstadoValidacionDocumento.PENDIENTE
            ),
            observacion_validacion=(
                ultimo_por_tipo[tipo].observacion_validacion if tipo in ultimo_por_tipo else None
            ),
        )
        for tipo in TIPOS_CHECKLIST_SOLICITUD
    ]
