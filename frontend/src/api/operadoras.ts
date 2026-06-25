import { api } from "@/lib/cliente";
import type { CableOperadora, CableOperadoraCrear } from "./tipos";

export function listarOperadoras() {
  return api.get<CableOperadora[]>("/operadoras").then((respuesta) => respuesta.data);
}

export function obtenerOperadora(id: number) {
  return api.get<CableOperadora>(`/operadoras/${id}`).then((respuesta) => respuesta.data);
}

export function crearOperadora(datos: CableOperadoraCrear) {
  return api.post<CableOperadora>("/operadoras", datos).then((respuesta) => respuesta.data);
}
