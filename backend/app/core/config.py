"""Configuración central de la aplicación, cargada desde variables de entorno (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    entorno: str = "desarrollo"
    debug: bool = True

    database_url: str = "mysql+pymysql://sgaie:sgaie_dev@localhost:3306/sgaie"

    jwt_secret_key: str = "clave-de-desarrollo-no-usar-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutos: int = 15
    jwt_refresh_token_dias: int = 7

    # Clave maestra para cifrado AES-256 de campos sensibles (base64, 32 bytes).
    aes_master_key: str = "MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE="

    cors_origenes: str = "http://localhost:5173"

    ldap_servidor: str = "ldap://dominio.cnel.local"
    ldap_base_dn: str = "DC=cnel,DC=local"
    ldap_bind_usuario_dominio: str = "cnel.local"
    ldap_usar_ssl: bool = False

    rate_limit_login: str = "5/minute"
    rate_limit_default: str = "100/minute"

    almacenamiento_documentos_dir: str = "./uploads"
    tamano_maximo_archivo_mb: int = 200

    tasa_interes_mora_anual: float = 0.1671

    @property
    def lista_cors_origenes(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origenes.split(",") if origen.strip()]


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
