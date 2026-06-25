/** Cliente HTTP (axios) con interceptores: adjunta el access token y renueva la sesión
 * automáticamente con el refresh token cuando el access token expira (§5.1). */
import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { guardarTokens, limpiarTokens, obtenerAccessToken, obtenerRefreshToken } from "./almacenTokens";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: BASE_URL });

// Cliente "crudo" sin interceptores, para no reintentar infinitamente la llamada de refresh.
const apiSinInterceptores = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = obtenerAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let renovacionEnCurso: Promise<string> | null = null;

async function renovarSesion(): Promise<string> {
  const refreshToken = obtenerRefreshToken();
  if (!refreshToken) {
    throw new Error("No hay sesión activa.");
  }
  const respuesta = await apiSinInterceptores.post<{
    access_token: string;
    refresh_token: string;
  }>("/auth/refresh", { refresh_token: refreshToken });
  guardarTokens({
    accessToken: respuesta.data.access_token,
    refreshToken: respuesta.data.refresh_token,
  });
  return respuesta.data.access_token;
}

api.interceptors.response.use(
  (respuesta) => respuesta,
  async (error: AxiosError) => {
    const peticionOriginal = error.config as
      | (InternalAxiosRequestConfig & { _reintentada?: boolean })
      | undefined;

    const esErrorDeAutenticacion = error.response?.status === 401;
    const noEsLoginNiRefresh = !peticionOriginal?.url?.includes("/auth/login")
      && !peticionOriginal?.url?.includes("/auth/refresh");

    if (esErrorDeAutenticacion && noEsLoginNiRefresh && peticionOriginal && !peticionOriginal._reintentada) {
      peticionOriginal._reintentada = true;
      try {
        renovacionEnCurso ??= renovarSesion();
        const nuevoAccessToken = await renovacionEnCurso;
        renovacionEnCurso = null;
        peticionOriginal.headers.Authorization = `Bearer ${nuevoAccessToken}`;
        return api(peticionOriginal);
      } catch (errorRenovacion) {
        renovacionEnCurso = null;
        limpiarTokens();
        window.location.assign("/login");
        return Promise.reject(errorRenovacion);
      }
    }

    return Promise.reject(error);
  },
);
