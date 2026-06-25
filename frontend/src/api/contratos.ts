import { api } from "@/lib/cliente";
import type { Contrato, ContratoActualizar, ContratoCrear } from "./tipos";

export function listarContratos() {
  return api.get<Contrato[]>("/contratos").then((respuesta) => respuesta.data);
}

export function obtenerContrato(id: number) {
  return api.get<Contrato>(`/contratos/${id}`).then((respuesta) => respuesta.data);
}

export function crearContrato(datos: ContratoCrear) {
  return api.post<Contrato>("/contratos", datos).then((respuesta) => respuesta.data);
}

export function actualizarContrato(id: number, datos: ContratoActualizar) {
  return api.put<Contrato>(`/contratos/${id}`, datos).then((respuesta) => respuesta.data);
}
