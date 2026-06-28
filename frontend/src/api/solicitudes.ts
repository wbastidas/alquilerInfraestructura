import { api } from "@/lib/cliente";
import type {
  Autorizacion,
  AutorizacionDecision,
  ChecklistItem,
  Documento,
  Solicitud,
  SolicitudActualizar,
  SolicitudCrear,
} from "./tipos";

export function listarSolicitudes() {
  return api.get<Solicitud[]>("/solicitudes").then((respuesta) => respuesta.data);
}

export function obtenerSolicitud(id: number) {
  return api.get<Solicitud>(`/solicitudes/${id}`).then((respuesta) => respuesta.data);
}

export function listarAutorizaciones(solicitudId: number) {
  return api
    .get<Autorizacion[]>(`/solicitudes/${solicitudId}/autorizaciones`)
    .then((respuesta) => respuesta.data);
}

export function listarDocumentosSolicitud(solicitudId: number) {
  return api
    .get<Documento[]>(`/solicitudes/${solicitudId}/documentos`)
    .then((respuesta) => respuesta.data);
}

export function obtenerChecklist(solicitudId: number) {
  return api
    .get<ChecklistItem[]>(`/solicitudes/${solicitudId}/checklist`)
    .then((respuesta) => respuesta.data);
}

export function crearSolicitud(datos: SolicitudCrear) {
  return api.post<Solicitud>("/solicitudes", datos).then((respuesta) => respuesta.data);
}

export function actualizarSolicitud(id: number, datos: SolicitudActualizar) {
  return api.put<Solicitud>(`/solicitudes/${id}`, datos).then((respuesta) => respuesta.data);
}

export function enviarSolicitud(id: number) {
  return api.post<Solicitud>(`/solicitudes/${id}/enviar`).then((respuesta) => respuesta.data);
}

export function decidirSolicitud(id: number, datos: AutorizacionDecision) {
  return api.post<Solicitud>(`/solicitudes/${id}/decidir`, datos).then((respuesta) => respuesta.data);
}

export function reenviarSolicitud(id: number) {
  return api.post<Solicitud>(`/solicitudes/${id}/reenviar`).then((respuesta) => respuesta.data);
}
