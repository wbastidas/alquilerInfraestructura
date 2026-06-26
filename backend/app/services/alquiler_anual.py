"""Servicio de AlquilerAnual + PostePorZona (§6.6, §7.2): alcance por UN y
cálculo automático del canon anual a partir del CatalogoCanon vigente."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UsuarioContexto
from app.core.exceptions import RecursoDuplicado, RecursoNoEncontrado
from app.models.alquiler_anual import AlquilerAnual, PostePorZona
from app.models.catalogo_canon import CatalogoCanon
from app.models.enums import EstadoPago
from app.schemas.alquiler_anual import (
    AlquilerAnualActualizar,
    AlquilerAnualCrear,
    PostePorZonaCrear,
)
from app.services.base import aplicar_alcance_un, verificar_pertenece_a_un

_CARGA_RELACIONES = (selectinload(AlquilerAnual.postes_por_zona),)


def resolver_canon_unitario(db: Session, tipo_zona, fecha: date | None = None) -> Decimal:
    """Valor vigente del canon para un tipo de zona a una fecha dada (§6.12)."""
    fecha = fecha or date.today()
    query = (
        select(CatalogoCanon)
        .where(CatalogoCanon.tipo_zona == tipo_zona, CatalogoCanon.vigente_desde <= fecha)
        .where((CatalogoCanon.vigente_hasta.is_(None)) | (CatalogoCanon.vigente_hasta >= fecha))
        .order_by(CatalogoCanon.vigente_desde.desc())
    )
    catalogo = db.scalars(query).first()
    if catalogo is None:
        raise RecursoNoEncontrado(
            f"No hay un valor de canon vigente para la zona {tipo_zona.value}."
        )
    return catalogo.valor


def _construir_zonas(db: Session, zonas: list[PostePorZonaCrear]) -> list[PostePorZona]:
    construidas = []
    for zona in zonas:
        canon_unitario = resolver_canon_unitario(db, zona.tipo_zona)
        subtotal = canon_unitario * zona.cantidad_postes
        construidas.append(
            PostePorZona(**zona.model_dump(), canon_unitario=canon_unitario, subtotal=subtotal)
        )
    return construidas


def _recalcular_totales(alquiler: AlquilerAnual) -> None:
    # Los defaults de columna (Decimal("0")) sólo se aplican en el flush/INSERT,
    # así que antes de eso el atributo Python puede seguir siendo None.
    recaudado = alquiler.monto_recaudado if alquiler.monto_recaudado is not None else Decimal("0")
    alquiler.monto_recaudado = recaudado
    alquiler.monto_facturado = sum(
        (zona.subtotal for zona in alquiler.postes_por_zona), Decimal("0")
    )
    alquiler.monto_pendiente_recaudar = alquiler.monto_facturado - recaudado
    if recaudado <= 0:
        alquiler.estado_pago = EstadoPago.PENDIENTE
    elif recaudado >= alquiler.monto_facturado:
        alquiler.estado_pago = EstadoPago.COMPLETO
    else:
        alquiler.estado_pago = EstadoPago.PARCIAL


def listar(db: Session, usuario_actual: UsuarioContexto) -> list[AlquilerAnual]:
    query = (
        select(AlquilerAnual)
        .options(*_CARGA_RELACIONES)
        .order_by(AlquilerAnual.anio.desc(), AlquilerAnual.cable_operadora_id)
    )
    query = aplicar_alcance_un(query, AlquilerAnual.unidad_negocio_id, usuario_actual)
    return list(db.scalars(query))


def obtener(db: Session, alquiler_anual_id: int, usuario_actual: UsuarioContexto) -> AlquilerAnual:
    query = (
        select(AlquilerAnual)
        .options(*_CARGA_RELACIONES)
        .where(AlquilerAnual.id == alquiler_anual_id)
    )
    alquiler = db.scalar(query)
    if alquiler is None:
        raise RecursoNoEncontrado("Registro de alquiler anual no encontrado.")
    verificar_pertenece_a_un(usuario_actual, alquiler.unidad_negocio_id)
    return alquiler


def crear(db: Session, datos: AlquilerAnualCrear, usuario_actual: UsuarioContexto) -> AlquilerAnual:
    verificar_pertenece_a_un(usuario_actual, datos.unidad_negocio_id)
    existente = db.scalar(
        select(AlquilerAnual).where(
            AlquilerAnual.cable_operadora_id == datos.cable_operadora_id,
            AlquilerAnual.anio == datos.anio,
        )
    )
    if existente is not None:
        raise RecursoDuplicado(f"Ya existe un alquiler anual {datos.anio} para esta operadora.")

    campos = datos.model_dump(exclude={"postes_por_zona"})
    alquiler = AlquilerAnual(**campos)
    alquiler.postes_por_zona = _construir_zonas(db, datos.postes_por_zona)
    _recalcular_totales(alquiler)
    db.add(alquiler)
    db.commit()
    db.refresh(alquiler)
    return alquiler


def actualizar(
    db: Session,
    alquiler_anual_id: int,
    datos: AlquilerAnualActualizar,
    usuario_actual: UsuarioContexto,
) -> AlquilerAnual:
    alquiler = obtener(db, alquiler_anual_id, usuario_actual)
    cambios = datos.model_dump(exclude_unset=True)
    zonas_nuevas = cambios.pop("postes_por_zona", None)
    if zonas_nuevas is not None:
        alquiler.postes_por_zona = _construir_zonas(
            db, [PostePorZonaCrear(**zona) for zona in zonas_nuevas]
        )
    for campo, valor in cambios.items():
        setattr(alquiler, campo, valor)
    _recalcular_totales(alquiler)
    db.commit()
    db.refresh(alquiler)
    return alquiler
