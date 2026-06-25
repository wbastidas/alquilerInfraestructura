/** Tipos TS que reflejan los esquemas Pydantic del backend (§6). Mantener sincronizados
 * manualmente con `backend/app/schemas/*` y `backend/app/models/enums.py`. */

export type CoberturaGeografica = "NACIONAL" | "REGIONAL" | "LOCAL";

export type EstadoContratoOperadora =
  | "ACTIVO"
  | "CADUCADO"
  | "SUSPENDIDO"
  | "EN_RENOVACION"
  | "EN_JURIDICO";

export type EstadoContrato =
  | "VIGENTE"
  | "EN_RENOVACION"
  | "TERMINADO"
  | "SUSPENDIDO"
  | "EN_JURIDICO";

export type TipoCuenta = "AD" | "LOCAL" | "PROVEEDOR";

export interface UnidadNegocio {
  id: number;
  codigo: string;
  nombre: string;
  provincia: string;
  activo: boolean;
}

export interface UnidadNegocioCrear {
  codigo: string;
  nombre: string;
  provincia: string;
  activo?: boolean;
}

export interface NombreComercial {
  id: number;
  nombre: string;
}

export interface TelefonoOperadora {
  id: number;
  numero: string;
  tipo: string | null;
}

export interface ResponsableTecnicoZona {
  id: number;
  nombre: string;
  cedula: string | null;
  cargo: string | null;
  telefono: string | null;
  correo: string | null;
  zona_cobertura: string | null;
}

export interface CableOperadora {
  id: number;
  numero_registro: string;
  nombre_empresa: string;
  ruc: string | null;
  cuenta_contrato: string | null;
  representante_legal: string | null;
  representante_cedula: string | null;
  titulo_habilitante_numero: string | null;
  titulo_habilitante_vigencia: string | null;
  arcotel_resolucion: string | null;
  servicios_autorizados: string | null;
  cobertura_geografica: CoberturaGeografica;
  correo: string | null;
  tipo_contrato: CoberturaGeografica;
  unidad_negocio_id: number;
  estado_contrato: EstadoContratoOperadora;
  fecha_firma_contrato: string | null;
  fecha_caducidad: string | null;
  nombres_comerciales: NombreComercial[];
  telefonos: TelefonoOperadora[];
  responsables_tecnicos: ResponsableTecnicoZona[];
}

export interface CableOperadoraCrear {
  numero_registro: string;
  nombre_empresa: string;
  ruc?: string | null;
  cuenta_contrato?: string | null;
  representante_legal?: string | null;
  representante_cedula?: string | null;
  titulo_habilitante_numero?: string | null;
  titulo_habilitante_vigencia?: string | null;
  arcotel_resolucion?: string | null;
  servicios_autorizados?: string | null;
  cobertura_geografica: CoberturaGeografica;
  correo?: string | null;
  tipo_contrato: CoberturaGeografica;
  unidad_negocio_id: number;
  nombres_comerciales?: { nombre: string }[];
  telefonos?: { numero: string; tipo?: string | null }[];
  responsables_tecnicos?: { nombre: string }[];
}

export interface Contrato {
  id: number;
  cable_operadora_id: number;
  unidad_negocio_id: number;
  numero_contrato: string;
  tipo_cobertura: CoberturaGeografica;
  fecha_suscripcion: string | null;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  poliza_numero: string | null;
  poliza_aseguradora: string | null;
  poliza_valor: string | null;
  poliza_vigencia_inicio: string | null;
  poliza_vigencia_fin: string | null;
  solicitud_id: number | null;
  informe_factibilidad_id: number | null;
  estado: EstadoContrato;
  total_postes: number;
  total_ductos_m: string;
  canon_anual_total: string;
}

export interface ContratoCrear {
  cable_operadora_id: number;
  unidad_negocio_id: number;
  numero_contrato: string;
  tipo_cobertura: CoberturaGeografica;
  fecha_suscripcion?: string | null;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
}

export interface ContratoActualizar {
  estado?: EstadoContrato;
  fecha_fin?: string | null;
  total_postes?: number;
  total_ductos_m?: string;
  canon_anual_total?: string;
}

export interface Usuario {
  id: number;
  username: string;
  nombre_completo: string;
  correo: string;
  tipo_cuenta: TipoCuenta;
  rol_id: number;
  unidad_negocio_id: number | null;
  cable_operadora_id: number | null;
  activo: boolean;
  ultimo_acceso: string | null;
}
