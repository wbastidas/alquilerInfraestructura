"""Adaptador desacoplado de pasarela de pagos (§7.4, método `PASARELA`).

# TODO: confirmar con el cliente el proveedor real de pasarela de pagos
# (PlaceToPay, PayPhone, Datafast, etc.) e implementar un adaptador concreto.
La integración real queda pendiente de confirmación; mientras tanto, `PasarelaSimulada`
permite ejercitar el flujo de `Pago` sin depender de un proveedor externo.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ResultadoPasarela:
    referencia_transaccion: str
    exitoso: bool
    mensaje: str | None = None


class PasarelaPago(ABC):
    """Interfaz que debe implementar cualquier proveedor de pasarela de pagos."""

    @abstractmethod
    def iniciar_pago(self, factura_id: int, monto: Decimal) -> ResultadoPasarela: ...


class PasarelaSimulada(PasarelaPago):
    """Implementación de referencia (sin proveedor real) para pruebas e integración local."""

    def iniciar_pago(self, factura_id: int, monto: Decimal) -> ResultadoPasarela:
        return ResultadoPasarela(
            referencia_transaccion=f"SIM-{factura_id}-{monto}",
            exitoso=True,
            mensaje="Transacción simulada (sin proveedor real de pasarela configurado).",
        )
