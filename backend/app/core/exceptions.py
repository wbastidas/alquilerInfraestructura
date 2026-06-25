"""Excepciones de dominio. Los routers las traducen a respuestas HTTP."""


class ErrorAplicacion(Exception):
    """Excepción base de la aplicación."""


class CredencialesInvalidas(ErrorAplicacion):
    pass


class UsuarioInactivo(ErrorAplicacion):
    pass


class TokenInvalido(ErrorAplicacion):
    pass


class PermisoDenegado(ErrorAplicacion):
    pass


class RecursoNoEncontrado(ErrorAplicacion):
    pass


class TransicionInvalida(ErrorAplicacion):
    """Transición de estado no permitida (p. ej. estados de Contrato, §7.1)."""
