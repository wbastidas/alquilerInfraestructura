import { api } from "@/lib/cliente";
import type { UnidadNegocio } from "./tipos";

export function listarUnidadesNegocio() {
  return api.get<UnidadNegocio[]>("/unidades-negocio").then((respuesta) => respuesta.data);
}
