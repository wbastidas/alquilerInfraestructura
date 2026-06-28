import { api } from "@/lib/cliente";
import type { DashboardConsolidado } from "./tipos";

export function obtenerConsolidado(anio?: number) {
  return api
    .get<DashboardConsolidado>("/dashboard/consolidado", { params: anio ? { anio } : undefined })
    .then((respuesta) => respuesta.data);
}
