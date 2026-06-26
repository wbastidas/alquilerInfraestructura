"""Pruebas del servicio de Solicitud (§6.7, §7.3, §7.5, §8): alcance por rol,
enrutamiento, y motor de autorizaciones multinivel."""

import pytest
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto
from app.core.checklist import TIPOS_CHECKLIST_SOLICITUD
from app.core.exceptions import PermisoDenegado, TransicionInvalida
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.enums import (
    CoberturaGeografica,
    DirigidaA,
    EstadoAutorizacion,
    EstadoContrato,
    EstadoSolicitud,
    EstadoValidacionDocumento,
    TipoSolicitud,
)
from app.models.rol import Rol
from app.models.unidad_negocio import UnidadNegocio
from app.models.usuario import Usuario
from app.schemas.autorizacion import AutorizacionDecision
from app.schemas.documento import DocumentoValidar
from app.schemas.solicitud import ContactoSolicitudCrear, RutaPropuestaCrear, SolicitudCrear
from app.services import documento as documento_servicio
from app.services import solicitud as servicio

from tests.conftest import contexto_de


def _crear_operadora(
    db_session: Session, unidad_negocio_id: int, numero_registro: str = "REG-100"
) -> CableOperadora:
    operadora = CableOperadora(
        numero_registro=numero_registro,
        nombre_empresa="Telecom Demo S.A.",
        cobertura_geografica=CoberturaGeografica.LOCAL,
        tipo_contrato=CoberturaGeografica.LOCAL,
        unidad_negocio_id=unidad_negocio_id,
    )
    db_session.add(operadora)
    db_session.commit()
    return operadora


def _crear_usuario_proveedor(
    db_session: Session, rol_proveedor: Rol, cable_operadora_id: int, username: str = "proveedor1"
) -> Usuario:
    usuario = Usuario(
        username=username,
        nombre_completo="Representante Proveedor",
        correo="proveedor@example.com",
        tipo_cuenta="PROVEEDOR",
        password_hash=None,
        rol_id=rol_proveedor.id,
        unidad_negocio_id=None,
        cable_operadora_id=cable_operadora_id,
        activo=True,
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


def _datos_solicitud(
    cable_operadora_id: int,
    tipo: TipoSolicitud = TipoSolicitud.NUEVO_CONTRATO,
    contrato_id: int | None = None,
    cobertura: CoberturaGeografica = CoberturaGeografica.LOCAL,
) -> SolicitudCrear:
    return SolicitudCrear(
        cable_operadora_id=cable_operadora_id,
        contrato_id=contrato_id,
        tipo=tipo,
        cobertura=cobertura,
        postes_solicitados=20,
        rutas_propuestas=[
            RutaPropuestaCrear(provincia="Guayas", ciudad="Guayaquil", total_postes=20)
        ],
        contactos=[ContactoSolicitudCrear(rol_contacto="Representante legal", nombre="Ana Pérez")],
    )


class _ArchivoFalso:
    def __init__(self, filename: str, content_type: str):
        self.filename = filename
        self.content_type = content_type


def _completar_checklist(
    db_session: Session,
    solicitud_id: int,
    usuario_prov: UsuarioContexto,
    usuario_interno: UsuarioContexto,
) -> None:
    """Sube y valida los §11 documentos requeridos para superar la compuerta documental."""
    for tipo in TIPOS_CHECKLIST_SOLICITUD:
        documento = documento_servicio.subir_para_solicitud(
            db_session,
            solicitud_id,
            tipo,
            _ArchivoFalso(f"{tipo.value.lower()}.pdf", "application/pdf"),
            b"contenido",
            usuario_prov,
        )
        documento_servicio.validar(
            db_session,
            documento.id,
            DocumentoValidar(estado_validacion=EstadoValidacionDocumento.VALIDADO),
            usuario_interno,
        )


def test_proveedor_crea_solicitud_nuevo_contrato_en_borrador(
    db_session: Session, unidad_negocio_a: UnidadNegocio, rol_proveedor: Rol
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)

    solicitud = servicio.crear(db_session, _datos_solicitud(operadora.id), usuario)

    assert solicitud.estado == EstadoSolicitud.BORRADOR
    assert solicitud.numero_referencia.startswith("SOL-")
    assert solicitud.unidad_negocio_id == unidad_negocio_a.id
    assert solicitud.dirigida_a == DirigidaA.ADMIN_UNIDAD_NEGOCIO
    assert len(solicitud.rutas_propuestas) == 1
    assert len(solicitud.contactos) == 1


def test_dirigida_a_regional_va_a_gerente_general(
    db_session: Session, unidad_negocio_a: UnidadNegocio, rol_proveedor: Rol
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)

    solicitud = servicio.crear(
        db_session,
        _datos_solicitud(operadora.id, cobertura=CoberturaGeografica.REGIONAL),
        usuario,
    )

    assert solicitud.dirigida_a == DirigidaA.GERENTE_GENERAL


def test_ampliacion_sin_contrato_id_falla_validacion():
    with pytest.raises(ValueError):
        SolicitudCrear(
            cable_operadora_id=1,
            tipo=TipoSolicitud.AMPLIACION,
            cobertura=CoberturaGeografica.LOCAL,
        )


def test_proveedor_no_puede_crear_solicitud_para_otra_operadora(
    db_session: Session, unidad_negocio_a: UnidadNegocio, rol_proveedor: Rol
):
    operadora_propia = _crear_operadora(db_session, unidad_negocio_a.id, "REG-100")
    operadora_ajena = _crear_operadora(db_session, unidad_negocio_a.id, "REG-200")
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora_propia.id)
    usuario = contexto_de(proveedor, rol_proveedor)

    with pytest.raises(PermisoDenegado):
        servicio.crear(db_session, _datos_solicitud(operadora_ajena.id), usuario)


def test_listar_alcance_por_rol(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    unidad_negocio_b: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
):
    operadora_a = _crear_operadora(db_session, unidad_negocio_a.id, "REG-100")
    operadora_b = _crear_operadora(db_session, unidad_negocio_b.id, "REG-200")
    proveedor_a = _crear_usuario_proveedor(db_session, rol_proveedor, operadora_a.id, "prov-a")
    proveedor_b = _crear_usuario_proveedor(db_session, rol_proveedor, operadora_b.id, "prov-b")

    servicio.crear(
        db_session, _datos_solicitud(operadora_a.id), contexto_de(proveedor_a, rol_proveedor)
    )
    servicio.crear(
        db_session, _datos_solicitud(operadora_b.id), contexto_de(proveedor_b, rol_proveedor)
    )

    assert len(servicio.listar(db_session, contexto_de(proveedor_a, rol_proveedor))) == 1
    assert len(servicio.listar(db_session, contexto_de(proveedor_b, rol_proveedor))) == 1
    assert len(servicio.listar(db_session, contexto_de(usuario_local, rol_un))) == 1


def test_enviar_transiciona_de_borrador_a_recepcion(
    db_session: Session, unidad_negocio_a: UnidadNegocio, rol_proveedor: Rol
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = servicio.crear(db_session, _datos_solicitud(operadora.id), usuario)

    enviada = servicio.enviar(db_session, solicitud.id, usuario)

    assert enviada.estado == EstadoSolicitud.RECEPCION


def test_enviar_solicitud_no_borrador_falla(
    db_session: Session, unidad_negocio_a: UnidadNegocio, rol_proveedor: Rol
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = servicio.crear(db_session, _datos_solicitud(operadora.id), usuario)
    servicio.enviar(db_session, solicitud.id, usuario)

    with pytest.raises(TransicionInvalida):
        servicio.enviar(db_session, solicitud.id, usuario)


def test_proveedor_no_puede_decidir(
    db_session: Session, unidad_negocio_a: UnidadNegocio, rol_proveedor: Rol
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    usuario = contexto_de(proveedor, rol_proveedor)
    solicitud = servicio.crear(db_session, _datos_solicitud(operadora.id), usuario)
    servicio.enviar(db_session, solicitud.id, usuario)

    with pytest.raises(PermisoDenegado):
        servicio.decidir(
            db_session,
            solicitud.id,
            AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
            usuario,
        )


def test_workflow_nuevo_contrato_recorre_todas_las_etapas_hasta_finalizada(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
    directorio_documentos,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    proveedor_ctx = contexto_de(proveedor, rol_proveedor)
    interno_ctx = contexto_de(usuario_local, rol_un)

    solicitud = servicio.crear(db_session, _datos_solicitud(operadora.id), proveedor_ctx)
    servicio.enviar(db_session, solicitud.id, proveedor_ctx)
    _completar_checklist(db_session, solicitud.id, proveedor_ctx, interno_ctx)

    estados_esperados = [
        EstadoSolicitud.REVISION_TECNICA,
        EstadoSolicitud.APROBACION_GERENCIAL,
        EstadoSolicitud.REVISION_JURIDICA,
        EstadoSolicitud.AUTORIZACION_FINAL,
        EstadoSolicitud.FINALIZADA,
    ]
    for esperado in estados_esperados:
        solicitud = servicio.decidir(
            db_session,
            solicitud.id,
            AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
            interno_ctx,
        )
        assert solicitud.estado == esperado

    historial = servicio.listar_autorizaciones(db_session, solicitud.id, interno_ctx)
    assert len(historial) == 5
    assert all(a.estado == EstadoAutorizacion.APROBADO for a in historial)


def test_workflow_ampliacion_omite_revision_juridica(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
    directorio_documentos,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    contrato = Contrato(
        cable_operadora_id=operadora.id,
        unidad_negocio_id=unidad_negocio_a.id,
        numero_contrato="CONT-900",
        tipo_cobertura=CoberturaGeografica.LOCAL,
        estado=EstadoContrato.VIGENTE,
    )
    db_session.add(contrato)
    db_session.commit()

    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    proveedor_ctx = contexto_de(proveedor, rol_proveedor)
    interno_ctx = contexto_de(usuario_local, rol_un)

    solicitud = servicio.crear(
        db_session,
        _datos_solicitud(operadora.id, tipo=TipoSolicitud.AMPLIACION, contrato_id=contrato.id),
        proveedor_ctx,
    )
    assert solicitud.dirigida_a == DirigidaA.ADMIN_CONTRATO
    servicio.enviar(db_session, solicitud.id, proveedor_ctx)
    _completar_checklist(db_session, solicitud.id, proveedor_ctx, interno_ctx)

    for _ in range(
        3
    ):  # RECEPCION -> REVISION_TECNICA -> APROBACION_GERENCIAL -> AUTORIZACION_FINAL
        solicitud = servicio.decidir(
            db_session,
            solicitud.id,
            AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
            interno_ctx,
        )
    assert solicitud.estado == EstadoSolicitud.AUTORIZACION_FINAL

    solicitud = servicio.decidir(
        db_session,
        solicitud.id,
        AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
        interno_ctx,
    )
    assert solicitud.estado == EstadoSolicitud.FINALIZADA


def test_observada_y_reenviada_vuelve_a_la_misma_etapa(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    proveedor_ctx = contexto_de(proveedor, rol_proveedor)
    interno_ctx = contexto_de(usuario_local, rol_un)

    solicitud = servicio.crear(db_session, _datos_solicitud(operadora.id), proveedor_ctx)
    servicio.enviar(db_session, solicitud.id, proveedor_ctx)

    observada = servicio.decidir(
        db_session,
        solicitud.id,
        AutorizacionDecision(estado=EstadoAutorizacion.OBSERVADO, comentario="Falta SIG"),
        interno_ctx,
    )
    assert observada.estado == EstadoSolicitud.OBSERVADA

    reenviada = servicio.reenviar(db_session, solicitud.id, proveedor_ctx)
    assert reenviada.estado == EstadoSolicitud.RECEPCION


def test_rechazada_es_terminal(
    db_session: Session,
    unidad_negocio_a: UnidadNegocio,
    rol_proveedor: Rol,
    rol_un: Rol,
    usuario_local: Usuario,
):
    operadora = _crear_operadora(db_session, unidad_negocio_a.id)
    proveedor = _crear_usuario_proveedor(db_session, rol_proveedor, operadora.id)
    proveedor_ctx = contexto_de(proveedor, rol_proveedor)
    interno_ctx = contexto_de(usuario_local, rol_un)

    solicitud = servicio.crear(db_session, _datos_solicitud(operadora.id), proveedor_ctx)
    servicio.enviar(db_session, solicitud.id, proveedor_ctx)

    rechazada = servicio.decidir(
        db_session,
        solicitud.id,
        AutorizacionDecision(estado=EstadoAutorizacion.RECHAZADO, comentario="No procede"),
        interno_ctx,
    )
    assert rechazada.estado == EstadoSolicitud.RECHAZADA

    with pytest.raises(TransicionInvalida):
        servicio.decidir(
            db_session,
            solicitud.id,
            AutorizacionDecision(estado=EstadoAutorizacion.APROBADO),
            interno_ctx,
        )
