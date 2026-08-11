import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { cerrarSesion, loginDominio, loginLocal } from "@/api/auth";
import { guardarTokens, limpiarTokens, obtenerAccessToken, obtenerRefreshToken } from "@/lib/almacenTokens";
import { decodificarAccessToken } from "./jwt";
import type { UsuarioContexto } from "./tipos";

interface ContextoAutenticacion {
  usuario: UsuarioContexto | null;
  cargando: boolean;
  entrarLocal: (username: string, password: string) => Promise<void>;
  entrarDominio: (username: string, password: string) => Promise<void>;
  salir: () => Promise<void>;
}

function usuarioDesdeAccessToken(accessToken: string): UsuarioContexto {
  const payload = decodificarAccessToken(accessToken);
  return {
    id: Number(payload.sub),
    username: payload.username,
    rol: payload.rol,
    unidadNegocioId: payload.unidad_negocio_id,
    cableOperadoraId: payload.cable_operadora_id,
    tipoCuenta: payload.tipo_cuenta,
  };
}

const ContextoAuth = createContext<ContextoAutenticacion | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioContexto | null>(() => {
    const token = obtenerAccessToken();
    if (!token) return null;
    try {
      return usuarioDesdeAccessToken(token);
    } catch {
      return null;
    }
  });
  const [cargando, setCargando] = useState(false);

  const entrarLocal = useCallback(async (username: string, password: string) => {
    setCargando(true);
    try {
      const tokens = await loginLocal(username, password);
      guardarTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      setUsuario(usuarioDesdeAccessToken(tokens.access_token));
    } finally {
      setCargando(false);
    }
  }, []);

  const entrarDominio = useCallback(async (username: string, password: string) => {
    setCargando(true);
    try {
      const tokens = await loginDominio(username, password);
      guardarTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      setUsuario(usuarioDesdeAccessToken(tokens.access_token));
    } finally {
      setCargando(false);
    }
  }, []);

  const salir = useCallback(async () => {
    const refreshToken = obtenerRefreshToken();
    try {
      if (refreshToken) await cerrarSesion(refreshToken);
    } finally {
      limpiarTokens();
      setUsuario(null);
    }
  }, []);

  const valor = useMemo(
    () => ({ usuario, cargando, entrarLocal, entrarDominio, salir }),
    [usuario, cargando, entrarLocal, entrarDominio, salir],
  );

  return <ContextoAuth.Provider value={valor}>{children}</ContextoAuth.Provider>;
}

export function useAuth(): ContextoAutenticacion {
  const contexto = useContext(ContextoAuth);
  if (!contexto) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider.");
  }
  return contexto;
}
