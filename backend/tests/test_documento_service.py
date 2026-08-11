"""Pruebas del servicio de Documento (§4.8, §6.8, §11): validación de carga, alcance por rol,
checklist documental y la compuerta de cumplimiento al 100% en el workflow de Solicitud."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.checklist import TIPOS_CHECKLIST_SOLICITUD
from app.core.exceptions import PermisoDenegado, TransicionInvalida
from app.models.enums import (
    CoberturaGeografica,
    EstadoAutorizacion,
    EstadoSolicitud,
    EstadoValidacionDocumento,
    TipoDocumento,
    TipoSolicitud,
)
from app.models.rol import Rol
from app.models.unidad_negocio import UnidadNegocio
from app.models.usuario import Usuario
from app.schemas.autorizacion import AutorizacionDecision
from app.schemas.documento import DocumentoValidar
from app.schemas.solicitud import ContactoSolicitudCrear, RutaPropuestaCrear, SolicitudCrear
from app.services import documento as servicio
from app.services import solicitud as solicitud_servicio

from tests.conftest import contexto_de
from tests.test_solicitud_service import _crear_operadora, _crear_usuario_proveedor


class _ArchivoFalso:
    def __init__(self, filename: str, content_type: str):
        self.filename = filename
        self.content_type = content_type


def _crear_solicitud(db_session: Session, cable_operadora_id: int, usuario):
    datos = SolicitudCrear(
        cable_operadora_id=cable_operadora_id,
        tipo=TipoSolicitud.NUEVO_CONTRATO,
        cobertura=CoberturaGeografica.LOCAL,
        postes_solicitados=20,
        rutas_propuestas=[
            RutaPropuestaCrear(provincia="Guayas", ciudad="Guayaquil", total_postes=20)
        ],
        contactos=[ContactoSolicitudCrear(rol_contacto="Representante legal", nombre="Ana Pérez")],
    )
    return solicitud_servicio.crear(db_session, datos, usuario)


def test_subir_documento_valido_para_solicitud(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario)

    documento = servicio.subir_para_solicitud(
        db_session,
        solicitud.id,
        TipoDocumento.RUC,
        _ArchivoFalso("ruc.pdf", "application/pdf"),
        b"contenido-pdf",
        usuario,
    )

    assert documento.estado_validacion == EstadoValidacionDocumento.PENDIENTE
    assert documento.nombre_archivo == "ruc.pdf"
    assert Path(documento.ruta_almacenamiento).exists()


def test_subir_documento_extension_no_permitida_falla(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario)

    with pytest.raises(ValueError):
        servicio.subir_para_solicitud(
            db_session,
            solicitud.id,
            TipoDocumento.RUC,
            _ArchivoFalso("virus.exe", "application/octet-stream"),
            b"contenido",
            usuario,
        )


def test_subir_documento_mime_no_coincide_con_extension_falla(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario)

    with pytest.raises(ValueError):
        servicio.subir_para_solicitud(
            db_session,
            solicitud.id,
            TipoDocumento.RUC,
            _ArchivoFalso("documento.pdf", "image/png"),
            b"contenido",
            usuario,
        )


def test_subir_documento_vacio_falla(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario)

    with pytest.raises(ValueError):
        servicio.subir_para_solicitud(
            db_session,
            solicitud.id,
            TipoDocumento.RUC,
            _ArchivoFalso("vacio.pdf", "application/pdf"),
            b"",
            usuario,
        )


def test_nombre_de_archivo_se_sanea_y_descarta_ruta(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario)

    documento = servicio.subir_para_solicitud(
        db_session,
        solicitud.id,
        TipoDocumento.RUC,
        _ArchivoFalso("../../etc/passwd raro!.pdf", "application/pdf"),
        b"contenido",
        usuario,
    )

    assert "/" not in documento.nombre_archivo
    assert ".." not in documento.nombre_archivo


def test_proveedor_de_otra_operadora_no_puede_subir(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora_propia = _crear_operadora(db_session, unidad_negocio_a.id, "REG-100")
    operadora_ajena = _crear_operadora(db_session, unidad_negocio_a.id, "REG-200")
    proveedor_propio = _crear_usuario_proveedor(db_session, rol_proveedor, operadora_propia.id)
    proveedor_ajeno = _crear_usuario_proveedor(
        db_session, rol_proveedor, operadora_ajena.id, "proveedor-ajeno"
    )
    usuario_propio = contexto_de(proveedor_propio, rol_proveedor)
    usuario_ajeno = contexto_de(proveedor_ajeno, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora_propia.id, usuario_propio)

    with pytest.raises(PermisoDenegado):
        servicio.subir_para_solicitud(
            db_session,
            solicitud.id,
            TipoDocumento.RUC,
            _ArchivoFalso("ruc.pdf", "application/pdf"),
            b"contenido",
            usuario_ajeno,
        )


def test_proveedor_no_puede_validar_su_propio_documento(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario)
    documento = servicio.subir_para_solicitud(
        db_session,
        solicitud.id,
        TipoDocumento.RUC,
        _ArchivoFalso("ruc.pdf", "application/pdf"),
        b"contenido",
        usuario,
    )

    with pytest.raises(PermisoDenegado):
        servicio.validar(
            db_session,
            documento.id,
            DocumentoValidar(estado_validacion=EstadoValidacionDocumento.VALIDADO),
            usuario,
        )


def test_personal_interno_valida_documento(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)
    usuario_interno = contexto_de(usuario_local, rol_un)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario_prov)
    documento = servicio.subir_para_solicitud(
        db_session,
        solicitud.id,
        TipoDocumento.RUC,
        _ArchivoFalso("ruc.pdf", "application/pdf"),
        b"contenido",
        usuario_prov,
    )

    validado = servicio.validar(
        db_session,
        documento.id,
        DocumentoValidar(
            estado_validacion=EstadoValidacionDocumento.VALIDADO, observacion_validacion="Ok"
        ),
        usuario_interno,
    )

    assert validado.estado_validacion == EstadoValidacionDocumento.VALIDADO
    assert validado.observacion_validacion == "Ok"


def test_checklist_refleja_pendientes_y_validados(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)
    usuario_interno = contexto_de(usuario_local, rol_un)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario_prov)

    documento = servicio.subir_para_solicitud(
        db_session,
        solicitud.id,
        TipoDocumento.RUC,
        _ArchivoFalso("ruc.pdf", "application/pdf"),
        b"contenido",
        usuario_prov,
    )
    servicio.validar(
        db_session,
        documento.id,
        DocumentoValidar(estado_validacion=EstadoValidacionDocumento.VALIDADO),
        usuario_interno,
    )

    checklist = servicio.obtener_checklist(db_session, solicitud.id, usuario_prov)
    por_tipo = {item.tipo_documento: item for item in checklist}

    assert por_tipo[TipoDocumento.RUC].estado_validacion == EstadoValidacionDocumento.VALIDADO
    assert por_tipo[TipoDocumento.RUC].documento_id == documento.id
    assert (
        por_tipo[TipoDocumento.TITULO_HABILITANTE].estado_validacion
        == EstadoValidacionDocumento.PENDIENTE
    )
    assert por_tipo[TipoDocumento.TITULO_HABILITANTE].documento_id is None


def test_checklist_usa_la_ultima_carga_por_tipo(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario)

    servicio.subir_para_solicitud(
        db_session,
        solicitud.id,
        TipoDocumento.RUC,
        _ArchivoFalso("ruc_v1.pdf", "application/pdf"),
        b"version-1",
        usuario,
    )
    segundo = servicio.subir_para_solicitud(
        db_session,
        solicitud.id,
        TipoDocumento.RUC,
        _ArchivoFalso("ruc_v2.pdf", "application/pdf"),
        b"version-2",
        usuario,
    )

    checklist = servicio.obtener_checklist(db_session, solicitud.id, usuario)
    item_ruc = next(item for item in checklist if item.tipo_documento == TipoDocumento.RUC)
    assert item_ruc.documento_id == segundo.id


def _completar_checklist(db_session: Session, solicitud_id, usuario_prov, usuario_interno) -> None:
    for tipo in TIPOS_CHECKLIST_SOLICITUD:
        documento = servicio.subir_para_solicitud(
            db_session,
            solicitud_id,
            tipo,
            _ArchivoFalso(f"{tipo.value.lower()}.pdf", "application/pdf"),
            b"contenido",
            usuario_prov,
        )
        servicio.validar(
            db_session,
            documento.id,
            DocumentoValidar(estado_validacion=EstadoValidacionDocumento.VALIDADO),
            usuario_interno,
        )


def test_decidir_bloquea_aprobacion_gerencial_sin_checklist_completo(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)
    usuario_interno = contexto_de(usuario_local, rol_un)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario_prov)
    solicitud_servicio.enviar(db_session, solicitud.id, usuario_prov)
    solicitud = solicitud_servicio.decidir(
        db_session,
        solicitud.id,
        AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
        usuario_interno,
    )  # RECEPCION -> REVISION_TECNICA

    with pytest.raises(TransicionInvalida):
        solicitud_servicio.decidir(
            db_session,
            solicitud.id,
            AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
            usuario_interno,
        )


def test_decidir_permite_aprobacion_gerencial_con_checklist_completo(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
    directorio_documentos: Path,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario_prov = contexto_de(proveedor, rol_proveedor)
    usuario_interno = contexto_de(usuario_local, rol_un)
    solicitud = _crear_solicitud(db_session, operadora.id, usuario_prov)
    solicitud_servicio.enviar(db_session, solicitud.id, usuario_prov)
    solicitud = solicitud_servicio.decidir(
        db_session,
        solicitud.id,
        AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
        usuario_interno,
    )  # RECEPCION -> REVISION_TECNICA

    _completar_checklist(db_session, solicitud.id, usuario_prov, usuario_interno)

    solicitud = solicitud_servicio.decidir(
        db_session,
        solicitud.id,
        AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
        usuario_interno,
    )

    assert solicitud.estado == EstadoSolicitud.APROBACION_GERENCIAL
