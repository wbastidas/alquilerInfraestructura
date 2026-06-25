import type { PayloadAccessToken } from "./tipos";

/** Decodifica el payload de un JWT sin validar la firma: la validación real ocurre
 * siempre en el backend (§5). Aquí solo se usa para derivar la identidad en la UI. */
export function decodificarAccessToken(token: string): PayloadAccessToken {
  const partes = token.split(".");
  if (partes.length !== 3) {
    throw new Error("Token con formato inválido.");
  }
  const payloadBase64 = partes[1].replace(/-/g, "+").replace(/_/g, "/");
  const json = decodeURIComponent(
    atob(payloadBase64)
      .split("")
      .map((caracter) => "%" + ("00" + caracter.charCodeAt(0).toString(16)).slice(-2))
      .join(""),
  );
  return JSON.parse(json) as PayloadAccessToken;
}

export function tokenExpirado(payload: PayloadAccessToken): boolean {
  return Date.now() >= payload.exp * 1000;
}
