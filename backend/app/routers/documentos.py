"""Endpoints de Documento (§4.8, §6.8, §11): carga validada y descarga auditada."""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auditoria.servicio import registrar_auditoria
from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.middlewares.rate_limit import limiter
from app.models.enums import AccionAuditoria, TipoDocumento
from app.schemas.documento import DocumentoRespuesta, DocumentoValidar
from app.services import documento as servicio

router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.post("", response_model=DocumentoRespuesta, status_code=201)
@limiter.limit("20/minute")
async def subir(
    request: Request,
    solicitud_id: int = Form(...),
    tipo_documento: TipoDocumento = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    contenido = await archivo.read()
    documento = servicio.subir_para_solicitud(
        db, solicitud_id, tipo_documento, archivo, contenido, usuario
    )
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        accion=AccionAuditoria.CREAR,
        entidad_tipo="Documento",
        entidad_id=documento.id,
        descripcion=f"Carga de {tipo_documento.value} para solicitud #{solicitud_id}",
        ip_origen=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return documento


@router.get("/{documento_id}")
def descargar(
    documento_id: int,
    request: Request,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    """Descarga auditada (§10): cada acceso al binario queda en LogAuditoria."""
    documento, contenido = servicio.descargar(db, documento_id, usuario)
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        accion=AccionAuditoria.DESCARGA,
        entidad_tipo="Documento",
        entidad_id=documento.id,
        descripcion=f"Descarga de {documento.nombre_archivo}",
        ip_origen=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return Response(
        content=contenido,
        media_type=documento.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{documento.nombre_archivo}"'},
    )


@router.post("/{documento_id}/validar", response_model=DocumentoRespuesta)
def validar(
    documento_id: int,
    datos: DocumentoValidar,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.validar(db, documento_id, datos, usuario)
