"""Servicio de Factura y Pago (§6.11, §7.4): emisión, registro de pagos, conciliación
bancaria, intereses por mora y reporte de morosidad.

Alcance por rol (regla de oro, §5.3):
    Proveedor   -> solo lectura de las facturas/pagos de su propia operadora.
    Unidad de Negocio -> lectura/escritura de las facturas de contratos de su propia UN.
    Matriz/Superadmin -> lectura global, sin escritura.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UsuarioContexto
from app.core.config import obtener_configuracion
from app.core.exceptions import (
    PermisoDenegado,
    RecursoDuplicado,
    RecursoNoEncontrado,
    TransicionInvalida,
)
from app.models.alquiler_anual import AlquilerAnual
from app.models.contrato import Contrato
from app.models.enums import EstadoFactura
from app.models.pago import Factura, Pago
from app.schemas.pago import FacturaCrear, PagoCrear

_CARGA_FACTURA = (selectinload(Factura.contrato), selectinload(Factura.pagos))


@dataclass
class ItemMorosidad:
    factura_id: int
    numero_factura: str
    cable_operadora_id: int
    fecha_vencimiento: date
    dias_mora: int
    saldo_pendiente: Decimal
    interes_mora: Decimal


def _verificar_acceso_factura(usuario: UsuarioContexto, factura: Factura) -> None:
    if usuario.es_matriz_o_superadmin:
        return
    if usuario.es_proveedor:
        if usuario.cable_operadora_id != factura.cable_operadora_id:
            raise PermisoDenegado("No tiene acceso a facturas de otra operadora.")
        return
    if usuario.unidad_negocio_id != factura.contrato.unidad_negocio_id:
        raise PermisoDenegado("No tiene acceso a facturas de otra Unidad de Negocio.")


def _saldo_pendiente(factura: Factura) -> Decimal:
    pagado = sum((p.monto for p in factura.pagos), Decimal("0"))
    return factura.total - pagado


def _recalcular_estado_factura(factura: Factura) -> None:
    """Reevalúa el estado de la factura a partir de sus pagos y vencimiento (§6.11)."""
    if factura.estado == EstadoFactura.ANULADA:
        return
    saldo = _saldo_pendiente(factura)
    pagado = factura.total - saldo
    if saldo <= 0:
        factura.estado = EstadoFactura.PAGADA
    elif factura.fecha_vencimiento < date.today():
        factura.estado = EstadoFactura.VENCIDA
    elif pagado > 0:
        factura.estado = EstadoFactura.PARCIAL
    else:
        factura.estado = EstadoFactura.EMITIDA


def listar_facturas(db: Session, usuario_actual: UsuarioContexto) -> list[Factura]:
    query = select(Factura).options(*_CARGA_FACTURA).order_by(Factura.fecha_emision.desc())
    if usuario_actual.es_matriz_o_superadmin:
        pass
    elif usuario_actual.es_proveedor:
        query = query.where(Factura.cable_operadora_id == usuario_actual.cable_operadora_id)
    else:
        query = query.join(Contrato, Factura.contrato_id == Contrato.id).where(
            Contrato.unidad_negocio_id == usuario_actual.unidad_negocio_id
        )
    return list(db.scalars(query))


def obtener_factura(db: Session, factura_id: int, usuario_actual: UsuarioContexto) -> Factura:
    query = select(Factura).options(*_CARGA_FACTURA).where(Factura.id == factura_id)
    factura = db.scalar(query)
    if factura is None:
        raise RecursoNoEncontrado("Factura no encontrada.")
    _verificar_acceso_factura(usuario_actual, factura)
    return factura


def crear_factura(db: Session, datos: FacturaCrear, usuario_actual: UsuarioContexto) -> Factura:
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no puede emitir facturas.")
    contrato = db.get(Contrato, datos.contrato_id)
    if contrato is None:
        raise RecursoNoEncontrado("Contrato no encontrado.")
    if contrato.cable_operadora_id != datos.cable_operadora_id:
        raise ValueError("El contrato no corresponde a la operadora indicada.")
    if not usuario_actual.es_matriz_o_superadmin:
        if usuario_actual.unidad_negocio_id != contrato.unidad_negocio_id:
            raise PermisoDenegado("No tiene acceso a registros de otra Unidad de Negocio.")
    if db.get(AlquilerAnual, datos.alquiler_anual_id) is None:
        raise RecursoNoEncontrado("Registro de alquiler anual no encontrado.")
    if db.scalar(select(Factura.id).where(Factura.numero_factura == datos.numero_factura)):
        raise RecursoDuplicado(f"Ya existe una factura con número {datos.numero_factura}.")

    factura = Factura(
        **datos.model_dump(),
        total=datos.monto + datos.iva,
        estado=EstadoFactura.EMITIDA,
    )
    db.add(factura)
    db.commit()
    db.refresh(factura)
    return factura


def registrar_pago(db: Session, datos: PagoCrear, usuario_actual: UsuarioContexto) -> Pago:
    """Registra un pago parcial o total contra una factura (§6.11, §7.4)."""
    if usuario_actual.es_proveedor:
        raise PermisoDenegado(
            "El proveedor no puede registrar pagos; debe hacerlo el personal de la "
            "Unidad de Negocio que conciliará el ingreso bancario."
        )
    factura = obtener_factura(db, datos.factura_id, usuario_actual)
    if factura.estado == EstadoFactura.ANULADA:
        raise TransicionInvalida("No se pueden registrar pagos sobre una factura anulada.")

    pago = Pago(
        monto=datos.monto,
        tipo=datos.tipo,
        metodo=datos.metodo,
        referencia_transaccion=datos.referencia_transaccion,
        fecha_pago=datos.fecha_pago,
        cable_operadora_id=factura.cable_operadora_id,
    )
    factura.pagos.append(pago)
    _recalcular_estado_factura(factura)
    db.commit()
    db.refresh(pago)
    return pago


def conciliar_pago(db: Session, pago_id: int, usuario_actual: UsuarioContexto) -> Pago:
    """Marca un pago como conciliado contra el estado de cuenta bancario (§7.4)."""
    if usuario_actual.es_proveedor:
        raise PermisoDenegado("El proveedor no puede conciliar pagos.")
    pago = db.get(Pago, pago_id)
    if pago is None:
        raise RecursoNoEncontrado("Pago no encontrado.")
    obtener_factura(db, pago.factura_id, usuario_actual)  # valida acceso por UN/operadora
    if pago.conciliado:
        raise TransicionInvalida("El pago ya se encuentra conciliado.")
    pago.conciliado = True
    pago.fecha_conciliacion = date.today()
    db.commit()
    db.refresh(pago)
    return pago


def calcular_interes_mora(factura: Factura, fecha_calculo: date | None = None) -> Decimal:
    """Interés por mora a la tasa activa referencial del BCE, parametrizable (§7.4, cl. 6.1.6)."""
    fecha_calculo = fecha_calculo or date.today()
    saldo = _saldo_pendiente(factura)
    if saldo <= 0 or factura.fecha_vencimiento >= fecha_calculo:
        return Decimal("0.00")
    dias_mora = (fecha_calculo - factura.fecha_vencimiento).days
    tasa = Decimal(str(obtener_configuracion().tasa_interes_mora_anual))
    interes = saldo * tasa * Decimal(dias_mora) / Decimal("365")
    return interes.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def reporte_morosidad(db: Session, usuario_actual: UsuarioContexto) -> list[ItemMorosidad]:
    """Facturas vencidas con saldo pendiente > 0, con su interés por mora calculado (§7.4)."""
    hoy = date.today()
    items: list[ItemMorosidad] = []
    for factura in listar_facturas(db, usuario_actual):
        if factura.estado == EstadoFactura.ANULADA:
            continue
        saldo = _saldo_pendiente(factura)
        if saldo <= 0 or factura.fecha_vencimiento >= hoy:
            continue
        items.append(
            ItemMorosidad(
                factura_id=factura.id,
                numero_factura=factura.numero_factura,
                cable_operadora_id=factura.cable_operadora_id,
                fecha_vencimiento=factura.fecha_vencimiento,
                dias_mora=(hoy - factura.fecha_vencimiento).days,
                saldo_pendiente=saldo,
                interes_mora=calcular_interes_mora(factura, hoy),
            )
        )
    return items
