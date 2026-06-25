"""Base declarativa de SQLAlchemy y tipo de columna cifrada (AES-256) para campos 🔒."""
from sqlalchemy import String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase

from app.core.security import cifrar_valor, descifrar_valor


class Base(DeclarativeBase):
    pass


class ValorCifrado(TypeDecorator):
    """Tipo de columna que cifra/descifra de forma transparente con AES-256-GCM.

    Usar en columnas marcadas con 🔒 en la especificación (cédulas, RUC, datos
    de contacto personales, referencias de transacción, etc.).
    """

    impl = String
    cache_ok = True

    def __init__(self, longitud_original: int = 255, *args, **kwargs) -> None:
        # El texto cifrado (base64 de nonce + ciphertext) ocupa más espacio que el original.
        super().__init__(*args, length=longitud_original * 4 + 100, **kwargs)

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return cifrar_valor(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return descifrar_valor(value)
