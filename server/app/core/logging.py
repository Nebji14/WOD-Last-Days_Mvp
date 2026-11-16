"""Journalisation structurée en JSON, avec identifiant de corrélation.

Chaque ligne de log porte l'identifiant de la requête en cours, ce qui permet
de relier une erreur signalée par un utilisateur à ses traces serveur.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

_EXTRA_FIELDS = ("method", "path", "status", "duration_ms", "account_id")


def current_request_id() -> str | None:
    """Retourne l'identifiant de la requête en cours, s'il existe."""
    return _request_id.get()


def bind_request_id(request_id: str) -> None:
    """Associe un identifiant de corrélation au contexte d'exécution courant."""
    _request_id.set(request_id)


class JsonFormatter(logging.Formatter):
    """Formate chaque enregistrement en une ligne JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": current_request_id(),
        }
        for field in _EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Installe le format JSON sur le logger racine.

    Les journaux d'accès d'Uvicorn sont coupés : le middleware de l'application
    produit sa propre ligne d'accès, sans paramètres d'URL.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("httpx").setLevel(logging.WARNING)
