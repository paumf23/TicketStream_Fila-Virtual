
# ═══════════════════════════════════════════════════════════════════════════════
# Jerarquía de Excepciones del Dominio
# ═══════════════════════════════════════════════════════════════════════════════
# Todas las excepciones de negocio heredan de VirtualQueueError.
# El handler global en middleware/error_handler.py las captura y convierte
# automáticamente en respuestas HTTP con el status_code correspondiente.
# ═══════════════════════════════════════════════════════════════════════════════


class VirtualQueueError(Exception):
    """Excepción base para todos los errores del dominio Virtual Queue."""

    status_code: int = 500

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(VirtualQueueError):
    """Recurso no encontrado (404)."""
    status_code = 404


class ConflictError(VirtualQueueError):
    """Conflicto con el estado actual del recurso (409)."""
    status_code = 409


class ForbiddenError(VirtualQueueError):
    """Acción no permitida para el usuario (403)."""
    status_code = 403


class BadRequestError(VirtualQueueError):
    """Datos o estado inválido en la solicitud (400)."""
    status_code = 400


class ValidationError(VirtualQueueError):
    """Error de validación de datos de entrada (422)."""
    status_code = 422


class RateLimitError(VirtualQueueError):
    """Límite de peticiones excedido (429)."""
    status_code = 429
