"""Servicio de Novedad y FotografiaNovedad (§6.13, §7.6): inspecciones programadas,
daños reportados y mantenimientos, con fotografías geolocalizadas.

Alcance por rol (regla de oro, §5.2/§5.3): a diferencia del expediente del proveedor,
una Novedad es generada por personal de CNEL EP sobre la infraestructura del
proveedor (inspección, daño, mantenimiento), no autoreportada por este. Por eso el
Proveedor tiene aquí solo lectura de las novedades de su propia operadora —igual
que se decidió para la validación de Documento (§11) y para Factura/Pago (§6.11)—
mientras que la Unidad de Negocio tiene lectura/escritura de las novedades de su
propia UN y Matriz/Superadmin lectura global.

Transiciones de estado permitidas (§6.13), siempre hacia adelante:
    PROGRAMADA -> EN_PROCESO -> EJECUTADA -> CERRADA
"""

import hashlib
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UsuarioContexto
from app.core.config import obtener_configuracion
from app.core.exceptions import PermisoDenegado, RecursoNoEncontrado, TransicionInvalida
from app.models.documento import Documento
from app.models.enums import (
    EntidadTipoDocumento,
    EstadoNovedad,
    EstadoValidacionDocumento,
    TipoDocumento,
)
from app.models.novedad import FotografiaNovedad, Novedad
from app.schemas.novedad import NovedadActualizar, NovedadCrear
from app.services.base import aplicar_alcance_un, verificar_pertenece_a_un
from app.services.documento import _sanitizar_nombre, _validar_archivo

_CARGA_RELACIONES = (selectinload(Novedad.fotografias),)

_TRANSICIONES_PERMITIDAS: dict[EstadoNovedad, set[EstadoNovedad]] = {
    EstadoNovedad.PROGRAMADA: {EstadoNovedad.EN_PROCESO},
    EstadoNovedad.EN_PROCESO: {EstadoNovedad.EJECUTADA},
    EstadoNovedad.EJECUTADA: {EstadoNovedad.CERRADA},
    EstadoNovedad.CERRADA: set(),
}


def _validar_transicion(actual: EstadoNovedad, nuevo: EstadoNovedad) -> None:
    if actual == nuevo:
        return
    if nuevo not in _TRANSICIONES_PERMITIDAS.get(actual, set()):
        raise TransicionInvalida(f"No se permite transicionar de {actual.value} a {nuevo.value}.")


def _verificar_acceso(usuario: UsuarioContexto, novedad: Novedad) -> None:
    if usuario.es_matriz_o_superadmin:
        return
    if usuario.es_proveedor:
        if usuario.cable_operadora_id != novedad.cable_operadora_id:
            raise PermisoDenegado("No tiene acceso a novedades de otra operadora.")
        return
    verificar_pertenece_a_un(usuario, novedad.unidad_negocio_id)


def listar(db: Session, usuario_actual: UsuarioContexto) -> list[Novedad]:
    query = select(Novedad).options(*_CARGA_RELACIONES).order_by(Novedad.id.desc())
    if usuario_actual.es_proveedor:
        query = query.where(Novedad.cable_operadora_id == usuario_actual.cable_operadora_id)
    else:
        query = aplicar_alcance_un(query, Novedad.unidad_negocio_id, usuario_actual)
    return list(db.scalars(query))


def obtener(db: Session, novedad_id: int, usuario_actual: UsuarioContexto) -> Novedad:
    query = select(Novedad).options(*_CARGA_RELACIONES).where(Novedad.id == novedad_id)
    novedad = db.scalar(query)
    if novedad is None:
        raise RecursoNoEncontrado("Novedad no encontrada.")
    _verificar_acceso(usuario_actual, novedad)
    return novedad


def crear(db: Session, datos: NovedadCrear, usuario_actual: UsuarioContexto) -> Novedad:
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no puede registrar novedades.")
    verificar_pertenece_a_un(usuario_actual, datos.unidad_negocio_id)

    novedad = Novedad(**datos.model_dump())
    db.add(novedad)
    db.commit()
    db.refresh(novedad)
    return novedad


def actualizar(
    db: Session, novedad_id: int, datos: NovedadActualizar, usuario_actual: UsuarioContexto
) -> Novedad:
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no puede modificar novedades.")
    novedad = obtener(db, novedad_id, usuario_actual)

    cambios = datos.model_dump(exclude_unset=True)
    nuevo_estado = cambios.pop("estado", None)
    if nuevo_estado is not None:
        _validar_transicion(novedad.estado, nuevo_estado)
        novedad.estado = nuevo_estado
    for campo, valor in cambios.items():
        setattr(novedad, campo, valor)

    db.commit()
    db.refresh(novedad)
    return novedad


def subir_fotografia(
    db: Session,
    novedad_id: int,
    archivo: UploadFile,
    contenido: bytes,
    usuario_actual: UsuarioContexto,
    latitud: Decimal | None = None,
    longitud: Decimal | None = None,
) -> FotografiaNovedad:
    """Carga una fotografía geolocalizada de la novedad (§6.13, §7.6)."""
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no puede cargar fotografías de novedades.")
    novedad = obtener(db, novedad_id, usuario_actual)

    nombre_saneado = _sanitizar_nombre(archivo.filename or "archivo")
    _validar_archivo(nombre_saneado, archivo.content_type or "", len(contenido))

    config = obtener_configuracion()
    directorio = Path(config.almacenamiento_documentos_dir) / "novedad" / str(novedad_id)
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / f"{uuid.uuid4().hex}_{nombre_saneado}"
    ruta.write_bytes(contenido)

    documento = Documento(
        entidad_tipo=EntidadTipoDocumento.NOVEDAD,
        entidad_id=novedad_id,
        tipo_documento=TipoDocumento.OTRO,
        nombre_archivo=nombre_saneado,
        ruta_almacenamiento=str(ruta),
        mime_type=archivo.content_type or "application/octet-stream",
        tamano_bytes=len(contenido),
        hash_sha256=hashlib.sha256(contenido).hexdigest(),
        estado_validacion=EstadoValidacionDocumento.PENDIENTE,
        creado_por=usuario_actual.id,
    )
    db.add(documento)
    db.flush()

    fotografia = FotografiaNovedad(
        novedad_id=novedad.id,
        documento_id=documento.id,
        latitud=latitud,
        longitud=longitud,
    )
    db.add(fotografia)
    db.commit()
    db.refresh(fotografia)
    return fotografia
