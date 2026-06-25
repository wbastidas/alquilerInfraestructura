/** Persistencia de tokens en localStorage (§5.1: access + refresh token). */

const CLAVE_ACCESS = "sgaie_access_token";
const CLAVE_REFRESH = "sgaie_refresh_token";

export interface ParTokens {
  accessToken: string;
  refreshToken: string;
}

export function guardarTokens(tokens: ParTokens): void {
  localStorage.setItem(CLAVE_ACCESS, tokens.accessToken);
  localStorage.setItem(CLAVE_REFRESH, tokens.refreshToken);
}

export function obtenerAccessToken(): string | null {
  return localStorage.getItem(CLAVE_ACCESS);
}

export function obtenerRefreshToken(): string | null {
  return localStorage.getItem(CLAVE_REFRESH);
}

export function limpiarTokens(): void {
  localStorage.removeItem(CLAVE_ACCESS);
  localStorage.removeItem(CLAVE_REFRESH);
}
