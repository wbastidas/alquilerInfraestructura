"""§11: documentación requerida del proveedor para el checklist de una Solicitud.

Constante compartida entre el servicio de Solicitud (que la usa para bloquear el avance a
APROBACION_GERENCIAL sin cumplimiento al 100%) y el servicio de Documento (que la usa para
construir la vista de checklist), evitando un import circular entre ambos servicios.
"""

from app.models.enums import TipoDocumento

TIPOS_CHECKLIST_SOLICITUD = [
    TipoDocumento.SOLICITUD_FORMAL,
    TipoDocumento.TITULO_HABILITANTE,
    TipoDocumento.DOC_SOCIETARIA,
    TipoDocumento.RUC,
    TipoDocumento.CEDULA_REP_LEGAL,
    TipoDocumento.COMPROBANTE_PAGO_ENERGIA,
    TipoDocumento.POLIZA,
    TipoDocumento.PLAN_EXPANSION,
    TipoDocumento.SIG_GEODATABASE,
    TipoDocumento.ESPEC_TECNICAS,
    TipoDocumento.LISTADO_CONTACTOS,
]
