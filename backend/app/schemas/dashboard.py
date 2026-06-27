"""Esquema de la vista consolidada del Dashboard (§7.2, §10)."""

from decimal import Decimal

from pydantic import BaseModel


class DashboardConsolidado(BaseModel):
    anio: int
    total_operadoras: int
    total_contratos_vigentes: int
    monto_facturado: Decimal
    monto_recaudado: Decimal
    monto_pendiente_recaudar: Decimal
    solicitudes_pendientes: int
    novedades_abiertas: int
    facturas_vencidas: int
    alertas_no_leidas: int
