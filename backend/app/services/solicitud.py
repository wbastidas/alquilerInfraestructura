"""Servicio de Solicitud (§6.7, §7.3, §7.5, §8): portal de proveedores y motor de
autorizaciones multinivel.

Alcance por rol (regla de oro, §5.3):
    Proveedor   -> solo sus propias solicitudes (`cable_operadora_id` propio).
    Unidad de Negocio -> solo las de su propia UN.
    Matriz/Superadmin -> lectura global, sin escritura (bloqueado en el router).

Workflow (§8): cada decisión sobre la etapa activa de la solicitud queda como un
registro `Autorizacion` inmutable (historial completo). Las ampliaciones (con
contrato existente) omiten `REVISION_JURIDICA`.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UsuarioContexto
from app.core.checklist import TIPOS_CHECKLIST_SOLICITUD
from app.core.exceptions import PermisoDenegado, RecursoNoEncontrado, TransicionInvalida
from app.models.autorizacion import Autorizacion
from app.models.cable_operadora import CableOperadora
from app.models.contrato import Contrato
from app.models.documento import Documento
from app.models.enums import (
    CoberturaGeografica,
    DirigidaA,
    EntidadTipoDocumento,
    EstadoAutorizacion,
    EstadoSolicitud,
    EstadoValidacionDocumento,
    EtapaAutorizacion,
    TipoSolicitud,
)
from app.models.solicitud import ContactoSolicitud, RutaPropuesta, Solicitud
from app.schemas.autorizacion import AutorizacionDecision
from app.schemas.solicitud import SolicitudActualizar, SolicitudCrear

_CARGA_RELACIONES = (
    selectinload(Solicitud.rutas_propuestas),
    selectinload(Solicitud.contactos),
)

_ORDEN_NUEVO_CONTRATO = [
    EtapaAutorizacion.RECEPCION,
    EtapaAutorizacion.REVISION_TECNICA,
    EtapaAutorizacion.APROBACION_GERENCIAL,
    EtapaAutorizacion.REVISION_JURIDICA,
    EtapaAutorizacion.AUTORIZACION_FINAL,
]
_ORDEN_AMPLIACION = [
    EtapaAutorizacion.RECEPCION,
    EtapaAutorizacion.REVISION_TECNICA,
    EtapaAutorizacion.APROBACION_GERENCIAL,
    EtapaAutorizacion.AUTORIZACION_FINAL,
]

_ESTADOS_TERMINALES = {
    EstadoSolicitud.BORRADOR,
    EstadoSolicitud.FINALIZADA,
    EstadoSolicitud.RECHAZADA,
}


def _orden_etapas(tipo: TipoSolicitud) -> list[EtapaAutorizacion]:
    return _ORDEN_AMPLIACION if tipo == TipoSolicitud.AMPLIACION else _ORDEN_NUEVO_CONTRATO


def _verificar_acceso(usuario: UsuarioContexto, solicitud: Solicitud) -> None:
    if usuario.es_matriz_o_superadmin:
        return
    if usuario.es_proveedor:
        if usuario.cable_operadora_id != solicitud.cable_operadora_id:
            raise PermisoDenegado("No tiene acceso a solicitudes de otra operadora.")
        return
    if usuario.unidad_negocio_id != solicitud.unidad_negocio_id:
        raise PermisoDenegado("No tiene acceso a solicitudes de otra Unidad de Negocio.")


def _generar_numero_referencia(db: Session, anio: int) -> str:
    prefijo = f"SOL-{anio}-"
    total = db.scalar(
        select(func.count())
        .select_from(Solicitud)
        .where(Solicitud.numero_referencia.like(f"{prefijo}%"))
    )
    return f"{prefijo}{(total or 0) + 1:05d}"


def _resolver_dirigida_a(datos: SolicitudCrear) -> DirigidaA:
    if datos.tipo == TipoSolicitud.AMPLIACION:
        return DirigidaA.ADMIN_CONTRATO
    if datos.cobertura == CoberturaGeografica.LOCAL:
        return DirigidaA.ADMIN_UNIDAD_NEGOCIO
    return DirigidaA.GERENTE_GENERAL


def _checklist_completo(db: Session, solicitud_id: int) -> bool:
    """§11: la solicitud no avanza a APROBACION_GERENCIAL sin cumplimiento documental al 100%."""
    documentos = db.scalars(
        select(Documento).where(
            Documento.entidad_tipo == EntidadTipoDocumento.SOLICITUD,
            Documento.entidad_id == solicitud_id,
        )
    )
    validados = {
        d.tipo_documento
        for d in documentos
        if d.estado_validacion == EstadoValidacionDocumento.VALIDADO
    }
    return all(tipo in validados for tipo in TIPOS_CHECKLIST_SOLICITUD)


def listar(db: Session, usuario_actual: UsuarioContexto) -> list[Solicitud]:
    query = select(Solicitud).options(*_CARGA_RELACIONES).order_by(Solicitud.fecha_creacion.desc())
    if usuario_actual.es_matriz_o_superadmin:
        pass
    elif usuario_actual.es_proveedor:
        query = query.where(Solicitud.cable_operadora_id == usuario_actual.cable_operadora_id)
    else:
        query = query.where(Solicitud.unidad_negocio_id == usuario_actual.unidad_negocio_id)
    return list(db.scalars(query))


def obtener(db: Session, solicitud_id: int, usuario_actual: UsuarioContexto) -> Solicitud:
    query = select(Solicitud).options(*_CARGA_RELACIONES).where(Solicitud.id == solicitud_id)
    solicitud = db.scalar(query)
    if solicitud is None:
        raise RecursoNoEncontrado("Solicitud no encontrada.")
    _verificar_acceso(usuario_actual, solicitud)
    return solicitud


def crear(db: Session, datos: SolicitudCrear, usuario_actual: UsuarioContexto) -> Solicitud:
    operadora = db.get(CableOperadora, datos.cable_operadora_id)
    if operadora is None:
        raise RecursoNoEncontrado("Cable operadora no encontrada.")
    if usuario_actual.es_proveedor:
        if usuario_actual.cable_operadora_id != operadora.id:
            raise PermisoDenegado("Solo puede crear solicitudes para su propia operadora.")
    elif not usuario_actual.es_matriz_o_superadmin:
        if usuario_actual.unidad_negocio_id != operadora.unidad_negocio_id:
            raise PermisoDenegado("No tiene acceso a registros de otra Unidad de Negocio.")

    if datos.contrato_id is not None:
        contrato = db.get(Contrato, datos.contrato_id)
        if contrato is None:
            raise RecursoNoEncontrado("Contrato no encontrado.")
        if contrato.cable_operadora_id != operadora.id:
            raise ValueError("El contrato no corresponde a la operadora indicada.")

    hoy = date.today()
    solicitud = Solicitud(
        numero_referencia=_generar_numero_referencia(db, hoy.year),
        tipo=datos.tipo,
        cable_operadora_id=operadora.id,
        contrato_id=datos.contrato_id,
        unidad_negocio_id=operadora.unidad_negocio_id,
        dirigida_a=_resolver_dirigida_a(datos),
        cobertura=datos.cobertura,
        provincias_involucradas=datos.provincias_involucradas,
        postes_solicitados=datos.postes_solicitados,
        ductos_solicitados_m=datos.ductos_solicitados_m,
        objetivo_proyecto=datos.objetivo_proyecto,
        tipo_redes=datos.tipo_redes,
        cronograma_inicio=datos.cronograma_inicio,
        cronograma_fin=datos.cronograma_fin,
        puesta_en_servicio=datos.puesta_en_servicio,
        estado=EstadoSolicitud.BORRADOR,
        fecha_creacion=hoy,
        rutas_propuestas=[RutaPropuesta(**r.model_dump()) for r in datos.rutas_propuestas],
        contactos=[ContactoSolicitud(**c.model_dump()) for c in datos.contactos],
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return solicitud


def actualizar(
    db: Session,
    solicitud_id: int,
    datos: SolicitudActualizar,
    usuario_actual: UsuarioContexto,
) -> Solicitud:
    solicitud = obtener(db, solicitud_id, usuario_actual)
    if solicitud.estado not in {EstadoSolicitud.BORRADOR, EstadoSolicitud.OBSERVADA}:
        raise TransicionInvalida(
            f"No se puede editar una solicitud en estado {solicitud.estado.value}."
        )
    cambios = datos.model_dump(exclude_unset=True)
    rutas_nuevas = cambios.pop("rutas_propuestas", None)
    contactos_nuevos = cambios.pop("contactos", None)
    if rutas_nuevas is not None:
        solicitud.rutas_propuestas = [RutaPropuesta(**ruta) for ruta in rutas_nuevas]
    if contactos_nuevos is not None:
        solicitud.contactos = [ContactoSolicitud(**contacto) for contacto in contactos_nuevos]
    for campo, valor in cambios.items():
        setattr(solicitud, campo, valor)
    db.commit()
    db.refresh(solicitud)
    return solicitud


def enviar(db: Session, solicitud_id: int, usuario_actual: UsuarioContexto) -> Solicitud:
    """Transición BORRADOR -> RECEPCION (§8): el proveedor envía la solicitud."""
    solicitud = obtener(db, solicitud_id, usuario_actual)
    if solicitud.estado != EstadoSolicitud.BORRADOR:
        raise TransicionInvalida("Solo una solicitud en BORRADOR puede enviarse a recepción.")
    solicitud.estado = EstadoSolicitud.RECEPCION
    db.commit()
    db.refresh(solicitud)
    return solicitud


def decidir(
    db: Session,
    solicitud_id: int,
    datos: AutorizacionDecision,
    usuario_actual: UsuarioContexto,
) -> Solicitud:
    """Registra la decisión (aprobar/observar/rechazar) sobre la etapa activa (§7.5, §8)."""
    solicitud = obtener(db, solicitud_id, usuario_actual)
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no participa en las decisiones del workflow interno.")
    try:
        etapa_actual = EtapaAutorizacion(solicitud.estado.value)
    except ValueError as exc:
        raise TransicionInvalida(
            f"La solicitud en estado {solicitud.estado.value} no admite decisiones de workflow."
        ) from exc

    if (
        datos.estado == EstadoAutorizacion.APROBADO
        and etapa_actual == EtapaAutorizacion.REVISION_TECNICA
        and not _checklist_completo(db, solicitud.id)
    ):
        raise TransicionInvalida(
            "No se puede avanzar a Aprobación Gerencial sin cumplimiento documental al 100% (§11)."
        )

    db.add(
        Autorizacion(
            solicitud_id=solicitud.id,
            etapa=etapa_actual,
            responsable_id=usuario_actual.id,
            estado=datos.estado,
            comentario=datos.comentario,
            fecha=date.today(),
        )
    )

    if datos.estado == EstadoAutorizacion.RECHAZADO:
        solicitud.estado = EstadoSolicitud.RECHAZADA
    elif datos.estado == EstadoAutorizacion.OBSERVADO:
        solicitud.estado = EstadoSolicitud.OBSERVADA
    else:  # APROBADO
        orden = _orden_etapas(solicitud.tipo)
        siguiente = orden.index(etapa_actual) + 1
        if siguiente < len(orden):
            solicitud.estado = EstadoSolicitud(orden[siguiente].value)
        else:
            solicitud.estado = EstadoSolicitud.FINALIZADA

    db.commit()
    db.refresh(solicitud)
    return solicitud


def reenviar(db: Session, solicitud_id: int, usuario_actual: UsuarioContexto) -> Solicitud:
    """Tras subsanar una solicitud OBSERVADA, vuelve a la etapa desde la que se observó (§8)."""
    solicitud = obtener(db, solicitud_id, usuario_actual)
    if solicitud.estado != EstadoSolicitud.OBSERVADA:
        raise TransicionInvalida("Solo se puede reenviar una solicitud observada.")
    ultima = db.scalar(
        select(Autorizacion)
        .where(Autorizacion.solicitud_id == solicitud.id)
        .order_by(Autorizacion.id.desc())
    )
    if ultima is None:
        raise RecursoNoEncontrado("No hay historial de autorizaciones para reenviar.")
    solicitud.estado = EstadoSolicitud(ultima.etapa.value)
    db.commit()
    db.refresh(solicitud)
    return solicitud


def listar_autorizaciones(
    db: Session, solicitud_id: int, usuario_actual: UsuarioContexto
) -> list[Autorizacion]:
    obtener(db, solicitud_id, usuario_actual)  # valida acceso y existencia
    query = (
        select(Autorizacion)
        .where(Autorizacion.solicitud_id == solicitud_id)
        .order_by(Autorizacion.id)
    )
    return list(db.scalars(query))
