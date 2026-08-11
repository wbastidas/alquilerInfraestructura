import { api } from "@/lib/cliente";
import type { AlquilerAnual, AlquilerAnualActualizar, AlquilerAnualCrear } from "./tipos";

export function listarAlquileresAnuales() {
  return api.get<AlquilerAnual[]>("/alquileres-anuales").then((respuesta) => respuesta.data);
}

export function obtenerAlquilerAnual(id: number) {
  return api.get<AlquilerAnual>(`/alquileres-anuales/${id}`).then((respuesta) => respuesta.data);
}

export function crearAlquilerAnual(datos: AlquilerAnualCrear) {
  return api.post<AlquilerAnual>("/alquileres-anuales", datos).then((respuesta) => respuesta.data);
}

export function actualizarAlquilerAnual(id: number, datos: AlquilerAnualActualizar) {
  return api
    .put<AlquilerAnual>(`/alquileres-anuales/${id}`, datos)
    .then((respuesta) => respuesta.data);
}
