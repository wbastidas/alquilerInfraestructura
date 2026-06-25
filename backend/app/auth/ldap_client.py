"""Autenticación contra dominio Windows / Active Directory vía LDAP (§5.1).

TODO: confirmar con cliente la estructura exacta de OU/grupos del Active
Directory institucional para mapear automáticamente grupos AD -> rol +
unidad_negocio. Por ahora, el bind LDAP solo valida credenciales; el mapeo
rol/UN del usuario AD se gestiona en la tabla `Usuario` (creada/actualizada
por el SUPERADMIN), igual que para cuentas locales.
"""
import logging

from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPException

from app.core.config import obtener_configuracion

logger = logging.getLogger(__name__)


def autenticar_contra_dominio(username: str, password: str) -> bool:
    """Intenta un bind LDAP con las credenciales dadas. No lanza excepciones de red:
    cualquier fallo de conexión/credenciales se traduce en `False` para no filtrar
    detalles internos del directorio al cliente."""
    config = obtener_configuracion()
    servidor = Server(config.ldap_servidor, get_info=ALL, use_ssl=config.ldap_usar_ssl)
    usuario_dn = f"{username}@{config.ldap_bind_usuario_dominio}"
    try:
        conexion = Connection(servidor, user=usuario_dn, password=password, auto_bind=True)
    except LDAPException:
        logger.warning("Fallo de autenticación LDAP para usuario %s", username)
        return False
    autenticado = conexion.bound
    conexion.unbind()
    return autenticado
