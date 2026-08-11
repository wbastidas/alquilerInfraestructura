import { api } from "@/lib/cliente";
import type { CatalogoCanon, CatalogoCanonCrear } from "./tipos";

export function listarCatalogoCanon() {
  return api.get<CatalogoCanon[]>("/catalogo-canon").then((respuesta) => respuesta.data);
}

export function crearCatalogoCanon(datos: CatalogoCanonCrear) {
  return api.post<CatalogoCanon>("/catalogo-canon", datos).then((respuesta) => respuesta.data);
}
