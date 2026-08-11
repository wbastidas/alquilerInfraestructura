import { api } from "@/lib/cliente";
import type { Factura, FacturaCrear, Pago, PagoCrear, ReporteMorosidadItem } from "./tipos";

export function listarFacturas() {
  return api.get<Factura[]>("/facturas").then((respuesta) => respuesta.data);
}

export function obtenerFactura(id: number) {
  return api.get<Factura>(`/facturas/${id}`).then((respuesta) => respuesta.data);
}

export function crearFactura(datos: FacturaCrear) {
  return api.post<Factura>("/facturas", datos).then((respuesta) => respuesta.data);
}

export function reporteMorosidad() {
  return api.get<ReporteMorosidadItem[]>("/facturas/morosidad").then((respuesta) => respuesta.data);
}

export function registrarPago(datos: PagoCrear) {
  return api.post<Pago>("/pagos", datos).then((respuesta) => respuesta.data);
}

export function conciliarPago(id: number) {
  return api.post<Pago>(`/pagos/${id}/conciliar`).then((respuesta) => respuesta.data);
}
