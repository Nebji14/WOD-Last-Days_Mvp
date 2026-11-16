"""Middlewares transverses : corrélation, journal d'accès, en-têtes de sécurité, origine."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.errors import ErrorCode
from app.core.logging import bind_request_id

logger = logging.getLogger("app.access")

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_REQUEST_ID_HEADER = "X-Request-ID"

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}
_HSTS = "max-age=63072000; includeSubDomains"

CallNext = Callable[[Request], Awaitable[Response]]


def register_middlewares(app: FastAPI, settings: Settings) -> None:
    """Installe les middlewares HTTP de l'application."""
    allowed_origins = frozenset(settings.allowed_origins)

    @app.middleware("http")
    async def request_context(request: Request, call_next: CallNext) -> Response:
        """Attribue un identifiant de corrélation et écrit la ligne d'accès."""
        request_id = uuid.uuid4().hex
        bind_request_id(request_id)
        started = time.perf_counter()

        if _is_forbidden_origin(request, allowed_origins):
            response: Response = JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": ErrorCode.FORBIDDEN_ORIGIN.value,
                        "message": "Origine de la requête refusée.",
                        "request_id": request_id,
                    }
                },
            )
        else:
            response = await call_next(request)

        response.headers[_REQUEST_ID_HEADER] = request_id
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if settings.is_production:
            response.headers.setdefault("Strict-Transport-Security", _HSTS)

        logger.info(
            "requête traitée",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return response


def _is_forbidden_origin(request: Request, allowed_origins: frozenset[str]) -> bool:
    """Protection CSRF : une requête modifiante doit venir d'une origine connue.

    Les navigateurs joignent l'en-tête ``Origin`` à toute requête modifiante
    inter-origines ; son absence correspond à un client non navigateur, qui ne
    porte pas les cookies d'un utilisateur.
    """
    if request.method in _SAFE_METHODS:
        return False
    origin = request.headers.get("origin")
    return origin is not None and origin.rstrip("/") not in allowed_origins
