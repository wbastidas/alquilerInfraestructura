import { api } from "@/lib/cliente";
import type { Rol } from "./tipos";

export function listarRoles() {
  return api.get<Rol[]>("/roles").then((respuesta) => respuesta.data);
}
