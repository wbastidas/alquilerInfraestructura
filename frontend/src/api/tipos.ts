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

export type TipoAlerta =
  | "VENCIMIENTO_CONTRATO"
  | "VENCIMIENTO_POLIZA"
  | "MOROSIDAD"
  | "VENCIMIENTO_TITULO"
  | "SIG_ANUAL_PENDIENTE";

export type SeveridadAlerta = "INFO" | "ADVERTENCIA" | "CRITICA";

export interface Alerta {
  id: number;
  tipo: TipoAlerta;
  entidad_tipo: string;
  entidad_id: number;
  unidad_negocio_id: number | null;
  mensaje: string;
  severidad: SeveridadAlerta;
  fecha_generacion: string;
  leida: boolean;
}

export interface DashboardConsolidado {
  anio: number;
  total_operadoras: number;
  total_contratos_vigentes: number;
  monto_facturado: string;
  monto_recaudado: string;
  monto_pendiente_recaudar: string;
  solicitudes_pendientes: number;
  novedades_abiertas: number;
  facturas_vencidas: number;
  alertas_no_leidas: number;
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

export interface UsuarioCrear {
  username: string;
  nombre_completo: string;
  correo: string;
  rol_id: number;
  unidad_negocio_id?: number | null;
  cable_operadora_id?: number | null;
  tipo_cuenta: TipoCuenta;
  password?: string | null;
}

export interface UsuarioActualizar {
  nombre_completo?: string;
  correo?: string;
  rol_id?: number;
  unidad_negocio_id?: number | null;
  activo?: boolean;
}

export interface Rol {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
}

export type TipoZona = "CAPITAL_PROVINCIAL" | "CABECERA_CANTONAL" | "OTRO_SECTOR";

export interface CatalogoCanon {
  id: number;
  tipo_zona: TipoZona;
  valor: string;
  vigente_desde: string;
  vigente_hasta: string | null;
  referencia_normativa: string | null;
}

export interface CatalogoCanonCrear {
  tipo_zona: TipoZona;
  valor: string;
  vigente_desde: string;
  vigente_hasta?: string | null;
  referencia_normativa?: string | null;
}

export type EstadoPagoAlquiler = "PENDIENTE" | "PARCIAL" | "COMPLETO";

export interface PostePorZona {
  id: number;
  provincia: string;
  canton: string;
  parroquia: string | null;
  tipo_zona: TipoZona;
  cantidad_postes: number;
  cantidad_ductos_m: string;
  canon_unitario: string;
  subtotal: string;
}

export interface PostePorZonaCrear {
  provincia: string;
  canton: string;
  parroquia?: string | null;
  tipo_zona: TipoZona;
  cantidad_postes?: number;
  cantidad_ductos_m?: string;
}

export interface AlquilerAnual {
  id: number;
  cable_operadora_id: number;
  contrato_id: number | null;
  unidad_negocio_id: number;
  anio: number;
  postes_sig: number;
  postes_fisicos: number;
  fecha_facturacion: string | null;
  observaciones: string | null;
  poliza_garantia_fecha: string | null;
  poliza_garantia_archivo_id: number | null;
  monto_facturado: string;
  monto_recaudado: string;
  monto_pendiente_recaudar: string;
  estado_pago: EstadoPagoAlquiler;
  postes_por_zona: PostePorZona[];
}

export interface AlquilerAnualCrear {
  cable_operadora_id: number;
  contrato_id?: number | null;
  unidad_negocio_id: number;
  anio: number;
  postes_sig?: number;
  postes_fisicos?: number;
  fecha_facturacion?: string | null;
  observaciones?: string | null;
  postes_por_zona?: PostePorZonaCrear[];
}

export interface AlquilerAnualActualizar {
  postes_sig?: number;
  postes_fisicos?: number;
  monto_recaudado?: string;
  fecha_facturacion?: string | null;
  observaciones?: string | null;
  postes_por_zona?: PostePorZonaCrear[];
}

export type TipoSolicitud = "NUEVO_CONTRATO" | "AMPLIACION";

export type DirigidaA = "GERENTE_GENERAL" | "ADMIN_UNIDAD_NEGOCIO" | "ADMIN_CONTRATO";

export type EstadoSolicitud =
  | "BORRADOR"
  | "RECEPCION"
  | "REVISION_TECNICA"
  | "APROBACION_GERENCIAL"
  | "REVISION_JURIDICA"
  | "AUTORIZACION_FINAL"
  | "FINALIZADA"
  | "OBSERVADA"
  | "RECHAZADA";

export type EtapaAutorizacion =
  | "RECEPCION"
  | "REVISION_TECNICA"
  | "APROBACION_GERENCIAL"
  | "REVISION_JURIDICA"
  | "AUTORIZACION_FINAL";

export type EstadoAutorizacion = "PENDIENTE" | "APROBADO" | "RECHAZADO" | "OBSERVADO";

export interface RutaPropuesta {
  id: number;
  provincia: string;
  ciudad: string | null;
  recinto: string | null;
  ruta: string | null;
  postes_usados: number;
  postes_nuevos: number;
  total_postes: number;
}

export interface RutaPropuestaCrear {
  provincia: string;
  ciudad?: string | null;
  recinto?: string | null;
  ruta?: string | null;
  postes_usados?: number;
  postes_nuevos?: number;
  total_postes?: number;
}

export interface ContactoSolicitud {
  id: number;
  rol_contacto: string;
  nombre: string;
  telefono: string | null;
  correo: string | null;
}

export interface ContactoSolicitudCrear {
  rol_contacto: string;
  nombre: string;
  telefono?: string | null;
  correo?: string | null;
}

export interface Solicitud {
  id: number;
  numero_referencia: string;
  tipo: TipoSolicitud;
  cable_operadora_id: number;
  contrato_id: number | null;
  unidad_negocio_id: number;
  cobertura: CoberturaGeografica;
  provincias_involucradas: string | null;
  postes_solicitados: number;
  ductos_solicitados_m: string;
  objetivo_proyecto: string | null;
  tipo_redes: string | null;
  cronograma_inicio: string | null;
  cronograma_fin: string | null;
  puesta_en_servicio: string | null;
  dirigida_a: DirigidaA;
  estado: EstadoSolicitud;
  fecha_creacion: string;
  rutas_propuestas: RutaPropuesta[];
  contactos: ContactoSolicitud[];
}

export interface SolicitudCrear {
  cable_operadora_id: number;
  contrato_id?: number | null;
  cobertura: CoberturaGeografica;
  provincias_involucradas?: string | null;
  postes_solicitados?: number;
  ductos_solicitados_m?: string;
  objetivo_proyecto?: string | null;
  tipo_redes?: string | null;
  cronograma_inicio?: string | null;
  cronograma_fin?: string | null;
  puesta_en_servicio?: string | null;
  tipo: TipoSolicitud;
  rutas_propuestas?: RutaPropuestaCrear[];
  contactos?: ContactoSolicitudCrear[];
}

export interface SolicitudActualizar {
  cobertura?: CoberturaGeografica;
  provincias_involucradas?: string | null;
  postes_solicitados?: number;
  ductos_solicitados_m?: string;
  objetivo_proyecto?: string | null;
  tipo_redes?: string | null;
  cronograma_inicio?: string | null;
  cronograma_fin?: string | null;
  puesta_en_servicio?: string | null;
  rutas_propuestas?: RutaPropuestaCrear[];
  contactos?: ContactoSolicitudCrear[];
}

export interface AutorizacionDecision {
  estado: "APROBADO" | "RECHAZADO" | "OBSERVADO";
  comentario?: string | null;
}

export interface Autorizacion {
  id: number;
  solicitud_id: number;
  etapa: EtapaAutorizacion;
  responsable_id: number | null;
  estado: EstadoAutorizacion;
  comentario: string | null;
  fecha: string;
}

export type TipoDocumento =
  | "SOLICITUD_FORMAL"
  | "TITULO_HABILITANTE"
  | "DOC_SOCIETARIA"
  | "RUC"
  | "CEDULA_REP_LEGAL"
  | "COMPROBANTE_PAGO_ENERGIA"
  | "POLIZA"
  | "PLAN_EXPANSION"
  | "SIG_GEODATABASE"
  | "ESPEC_TECNICAS"
  | "LISTADO_CONTACTOS"
  | "CONTRATO_FIRMADO"
  | "INFORME_FACTIBILIDAD"
  | "FOTO_PLACAS"
  | "OTRO";

export type EstadoValidacionDocumento = "PENDIENTE" | "VALIDADO" | "OBSERVADO" | "RECHAZADO";

export interface Documento {
  id: number;
  entidad_id: number;
  tipo_documento: TipoDocumento;
  nombre_archivo: string;
  mime_type: string;
  tamano_bytes: number;
  hash_sha256: string;
  estado_validacion: EstadoValidacionDocumento;
  observacion_validacion: string | null;
}

export interface DocumentoValidar {
  estado_validacion: "VALIDADO" | "OBSERVADO" | "RECHAZADO";
  observacion_validacion?: string | null;
}

export interface ChecklistItem {
  tipo_documento: TipoDocumento;
  documento_id: number | null;
  estado_validacion: EstadoValidacionDocumento;
  observacion_validacion: string | null;
}

export type EstadoFactura = "EMITIDA" | "PAGADA" | "VENCIDA" | "PARCIAL" | "ANULADA";

export type TipoPago = "PARCIAL" | "TOTAL";

export type MetodoPago = "TRANSFERENCIA" | "DEPOSITO" | "CHEQUE" | "TARJETA" | "VENTANILLA" | "PASARELA";

export interface Factura {
  id: number;
  cable_operadora_id: number;
  contrato_id: number;
  alquiler_anual_id: number;
  numero_factura: string;
  fecha_emision: string;
  fecha_vencimiento: string;
  monto: string;
  iva: string;
  total: string;
  estado: EstadoFactura;
  archivo_xml_id: number | null;
  archivo_pdf_id: number | null;
}

export interface FacturaCrear {
  cable_operadora_id: number;
  contrato_id: number;
  alquiler_anual_id: number;
  numero_factura: string;
  fecha_emision: string;
  fecha_vencimiento: string;
  monto: string;
  iva?: string;
}

export interface Pago {
  id: number;
  factura_id: number;
  cable_operadora_id: number;
  monto: string;
  tipo: TipoPago;
  metodo: MetodoPago;
  referencia_transaccion: string | null;
  fecha_pago: string;
  conciliado: boolean;
  fecha_conciliacion: string | null;
}

export interface PagoCrear {
  factura_id: number;
  monto: string;
  tipo: TipoPago;
  metodo: MetodoPago;
  referencia_transaccion?: string | null;
  fecha_pago: string;
}

export interface ReporteMorosidadItem {
  factura_id: number;
  numero_factura: string;
  cable_operadora_id: number;
  fecha_vencimiento: string;
  dias_mora: number;
  saldo_pendiente: string;
  interes_mora: string;
}

export type TipoNovedad = "INSPECCION_PROGRAMADA" | "DANO_REPORTADO" | "MANTENIMIENTO";

export type EstadoNovedad = "PROGRAMADA" | "EN_PROCESO" | "EJECUTADA" | "CERRADA";

export interface FotografiaNovedad {
  id: number;
  novedad_id: number;
  documento_id: number;
  latitud: string | null;
  longitud: string | null;
}

export interface Novedad {
  id: number;
  cable_operadora_id: number;
  contrato_id: number | null;
  unidad_negocio_id: number;
  tipo: TipoNovedad;
  descripcion: string | null;
  fecha_programada: string | null;
  estado: EstadoNovedad;
  fecha_ejecucion: string | null;
  latitud: string | null;
  longitud: string | null;
  ficha_informe_id: number | null;
  fotografias: FotografiaNovedad[];
}

export interface NovedadCrear {
  cable_operadora_id: number;
  contrato_id?: number | null;
  unidad_negocio_id: number;
  tipo: TipoNovedad;
  descripcion?: string | null;
  fecha_programada?: string | null;
  latitud?: string | null;
  longitud?: string | null;
}

export interface NovedadActualizar {
  estado?: EstadoNovedad;
  descripcion?: string | null;
  fecha_ejecucion?: string | null;
  latitud?: string | null;
  longitud?: string | null;
}
