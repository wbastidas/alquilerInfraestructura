import { api } from "@/lib/cliente";
import type { FotografiaNovedad, Novedad, NovedadActualizar, NovedadCrear } from "./tipos";

export function listarNovedades() {
  return api.get<Novedad[]>("/novedades").then((respuesta) => respuesta.data);
}

export function obtenerNovedad(id: number) {
  return api.get<Novedad>(`/novedades/${id}`).then((respuesta) => respuesta.data);
}

export function crearNovedad(datos: NovedadCrear) {
  return api.post<Novedad>("/novedades", datos).then((respuesta) => respuesta.data);
}

export function actualizarNovedad(id: number, datos: NovedadActualizar) {
  return api.put<Novedad>(`/novedades/${id}`, datos).then((respuesta) => respuesta.data);
}

export function subirFotografiaNovedad(
  novedadId: number,
  archivo: File,
  latitud?: string,
  longitud?: string,
) {
  const datosFormulario = new FormData();
  datosFormulario.append("archivo", archivo);
  if (latitud) datosFormulario.append("latitud", latitud);
  if (longitud) datosFormulario.append("longitud", longitud);
  return api
    .post<FotografiaNovedad>(`/novedades/${novedadId}/fotografias`, datosFormulario, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((respuesta) => respuesta.data);
}
