"""Endpoints de Factura y Pago (§6.11, §7.4, §10): emisión, registro de pagos,
conciliación bancaria y reporte de morosidad."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.schemas.pago import (
    FacturaCrear,
    FacturaRespuesta,
    PagoCrear,
    PagoRespuesta,
    ReporteMorosidadItem,
)
from app.services import pago as servicio

router = APIRouter(tags=["pagos"])


@router.get("/facturas", response_model=list[FacturaRespuesta])
def listar_facturas(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.listar_facturas(db, usuario)


@router.get("/facturas/morosidad", response_model=list[ReporteMorosidadItem])
def reporte_morosidad(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.reporte_morosidad(db, usuario)


@router.get("/facturas/{factura_id}", response_model=FacturaRespuesta)
def obtener_factura(
    factura_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener_factura(db, factura_id, usuario)


@router.post("/facturas", response_model=FacturaRespuesta, status_code=201)
def crear_factura(
    datos: FacturaCrear,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.crear_factura(db, datos, usuario)


@router.post("/pagos", response_model=PagoRespuesta, status_code=201)
def registrar_pago(
    datos: PagoCrear,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.registrar_pago(db, datos, usuario)


@router.post("/pagos/{pago_id}/conciliar", response_model=PagoRespuesta)
def conciliar_pago(
    pago_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.conciliar_pago(db, pago_id, usuario)
