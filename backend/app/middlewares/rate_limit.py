"""Rate limiting por IP en endpoints sensibles (§4.3): login, portal público, subida de archivos."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import obtener_configuracion

config = obtener_configuracion()

# TODO: confirmar con cliente backend de almacenamiento para producción (Redis recomendado
# para despliegues con varios workers Uvicorn); en memoria es suficiente para un solo proceso.
limiter = Limiter(key_func=get_remote_address, default_limits=[config.rate_limit_default])
