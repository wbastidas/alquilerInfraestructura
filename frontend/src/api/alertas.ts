import { api } from "@/lib/cliente";
import type { Alerta } from "./tipos";

export function listarAlertas() {
  return api.get<Alerta[]>("/alertas").then((respuesta) => respuesta.data);
}

export function marcarAlertaLeida(id: number) {
  return api.patch<Alerta>(`/alertas/${id}/leida`).then((respuesta) => respuesta.data);
}
