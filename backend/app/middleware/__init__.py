
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import VirtualQueueError

logger = logging.getLogger("app.error_handler")


def register_error_handlers(app: FastAPI) -> None:
    """Registra los handlers de errores globales en la app FastAPI."""

    @app.exception_handler(VirtualQueueError)
    async def domain_error_handler(
        request: Request, exc: VirtualQueueError
    ) -> JSONResponse:
        logger.warning(
            f"{exc.__class__.__name__}: {exc.message} | "
            f"path={request.url.path} method={request.method}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error_type": exc.__class__.__name__,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append({
                "campo": field,
                "mensaje": error["msg"],
                "tipo": error["type"],
            })

        logger.warning(
            f"ValidationError: {len(errors)} error(es) | "
            f"path={request.url.path}"
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Error de validación en los datos enviados.",
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            f"Error no controlado: {exc.__class__.__name__}: {exc} | "
            f"path={request.url.path} method={request.method}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor. Intente nuevamente más tarde.",
                "error_type": "InternalServerError",
            },
        )
