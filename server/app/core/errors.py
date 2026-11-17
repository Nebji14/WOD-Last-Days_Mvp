"""Erreurs applicatives et format d'erreur unique de l'API.

Toute réponse d'erreur a la forme ::

    {"error": {"code": "...", "message": "...", "request_id": "...", "details": [...]}}

Le client traduit ``code`` en libellé ; ``message`` reste générique et ne
contient jamais de détail interne.
"""

import logging
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import current_request_id

logger = logging.getLogger(__name__)


class ErrorCode(StrEnum):
    """Codes d'erreur stables exposés au client."""

    VALIDATION_ERROR = "validation_error"
    INVALID_CREDENTIALS = "invalid_credentials"
    NOT_AUTHENTICATED = "not_authenticated"
    FORBIDDEN = "forbidden"
    FORBIDDEN_ORIGIN = "forbidden_origin"
    WRONG_PORTAL_GM = "wrong_portal_gm"
    WRONG_PORTAL_PLAYER = "wrong_portal_player"
    GOOGLE_FAILED = "google_failed"
    USERNAME_TAKEN = "username_taken"
    USERNAME_INVALID = "username_invalid"
    PASSWORD_MISMATCH = "password_mismatch"
    PASSWORD_TOO_WEAK = "password_too_weak"
    RATE_LIMITED = "rate_limited"
    NOT_FOUND = "not_found"
    MESSAGE_DELETED = "message_deleted"
    RULE_VIOLATION = "rule_violation"
    EDIT_CONFLICT = "edit_conflict"
    UNSUPPORTED_IMAGE = "unsupported_image"
    IMAGE_TOO_LARGE = "image_too_large"
    FOLDER_CYCLE = "folder_cycle"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INTERNAL_ERROR = "internal_error"


class AppError(Exception):
    """Erreur métier ou d'accès, convertie en réponse HTTP.

    Args:
        code: code stable exposé au client.
        message: message générique, sans donnée sensible.
        status_code: statut HTTP de la réponse.
        details: précisions structurées facultatives (champs en erreur, règles).
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _error_response(
    status_code: int,
    code: ErrorCode,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Construit la réponse d'erreur au format unique."""
    body: dict[str, Any] = {
        "code": code.value,
        "message": message,
        "request_id": current_request_id(),
    }
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


async def _handle_app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)  # noqa: S101 - garanti par l'enregistrement du handler
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def _handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    """Signale les champs invalides sans jamais renvoyer la valeur saisie."""
    assert isinstance(exc, RequestValidationError)  # noqa: S101
    details = [
        {"field": ".".join(str(part) for part in error["loc"][1:]), "rule": error["type"]}
        for error in exc.errors()
    ]
    return _error_response(
        422, ErrorCode.VALIDATION_ERROR, "Les données envoyées sont invalides.", details
    )


async def _handle_http_exception(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101
    code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.INTERNAL_ERROR
    message = "Ressource introuvable." if exc.status_code == 404 else "Requête refusée."
    return _error_response(exc.status_code, code, message)


async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    """Journalise l'exception complète et ne renvoie qu'un message générique."""
    logger.error("Erreur inattendue", exc_info=exc)
    return _error_response(500, ErrorCode.INTERNAL_ERROR, "Une erreur interne est survenue.")


def register_error_handlers(app: FastAPI) -> None:
    """Enregistre les gestionnaires d'erreurs centralisés sur l'application."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)
