"""Modelos SQLAlchemy del modelo de datos completo (§6 de la especificación).

Se importan todos los módulos de modelos aquí para que Alembic (autogenerate)
y `Base.metadata.create_all` descubran todas las tablas a través de
`Base.metadata`.
"""
from app.models.alerta import Alerta
from app.models.alquiler_anual import AlquilerAnual, PostePorZona
from app.models.autorizacion import AdjuntoAutorizacion, Autorizacion
from app.models.cable_operadora import (
    CableOperadora,
    NombreComercial,
    ResponsableTecnicoZona,
    TelefonoOperadora,
)
from app.models.catalogo_canon import CatalogoCanon
from app.models.contrato import Contrato
from app.models.documento import Documento
from app.models.informe_factibilidad import InformeFactibilidad, UbicacionInformeFactibilidad
from app.models.log_auditoria import LogAuditoria
from app.models.novedad import FotografiaNovedad, Novedad
from app.models.pago import Factura, Pago
from app.models.rol import Permiso, Rol, RolPermiso
from app.models.solicitud import ContactoSolicitud, RutaPropuesta, Solicitud
from app.models.token_refresco import TokenRefrescoRevocado
from app.models.unidad_negocio import UnidadNegocio
from app.models.usuario import Usuario

__all__ = [
    "Alerta",
    "AlquilerAnual",
    "PostePorZona",
    "Autorizacion",
    "AdjuntoAutorizacion",
    "CableOperadora",
    "NombreComercial",
    "ResponsableTecnicoZona",
    "TelefonoOperadora",
    "CatalogoCanon",
    "Contrato",
    "Documento",
    "InformeFactibilidad",
    "UbicacionInformeFactibilidad",
    "LogAuditoria",
    "Novedad",
    "FotografiaNovedad",
    "Factura",
    "Pago",
    "Rol",
    "Permiso",
    "RolPermiso",
    "Solicitud",
    "RutaPropuesta",
    "ContactoSolicitud",
    "UnidadNegocio",
    "Usuario",
    "TokenRefrescoRevocado",
]
