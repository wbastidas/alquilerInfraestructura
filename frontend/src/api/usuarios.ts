import { api } from "@/lib/cliente";
import type { Usuario, UsuarioActualizar, UsuarioCrear } from "./tipos";

export function listarUsuarios() {
  return api.get<Usuario[]>("/usuarios").then((respuesta) => respuesta.data);
}

export function crearUsuario(datos: UsuarioCrear) {
  return api.post<Usuario>("/usuarios", datos).then((respuesta) => respuesta.data);
}

export function actualizarUsuario(id: number, datos: UsuarioActualizar) {
  return api.put<Usuario>(`/usuarios/${id}`, datos).then((respuesta) => respuesta.data);
}
