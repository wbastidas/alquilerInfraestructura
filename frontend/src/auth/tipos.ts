export interface UsuarioContexto {
  id: number;
  username: string;
  rol: string;
  unidadNegocioId: number | null;
  tipoCuenta: string;
}

export interface PayloadAccessToken {
  sub: string;
  username: string;
  rol: string;
  unidad_negocio_id: number | null;
  tipo_cuenta: string;
  tipo_token: string;
  exp: number;
}
