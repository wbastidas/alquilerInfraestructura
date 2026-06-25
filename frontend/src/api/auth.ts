import { api } from "@/lib/cliente";

export interface RespuestaTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function loginLocal(username: string, password: string) {
  return api
    .post<RespuestaTokens>("/auth/login", { username, password })
    .then((respuesta) => respuesta.data);
}

export function loginDominio(username: string, password: string) {
  return api
    .post<RespuestaTokens>("/auth/login/ad", { username, password })
    .then((respuesta) => respuesta.data);
}

export function cerrarSesion(refreshToken: string) {
  return api.post("/auth/logout", { refresh_token: refreshToken });
}
