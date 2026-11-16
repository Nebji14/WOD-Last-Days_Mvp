"""Dépendances FastAPI : conteneur de services, compte courant, limitation de débit."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.core.rate_limit import RateLimiter
from app.core.security import ACCESS_COOKIE, InvalidTokenError, TokenVerifier
from app.domain.accounts import Account, Role
from app.realtime.hub import ConnectionHub
from app.realtime.tickets import TicketStore
from app.services.auth import AuthService
from app.services.characters import CharacterService
from app.services.chat import ChatService
from app.services.sheet_items import SheetItemService
from app.services.table import TableService


@dataclass(frozen=True, slots=True)
class Container:
    """Services partagés par les routes, construits au démarrage de l'application."""

    settings: Settings
    auth_service: AuthService
    token_verifier: TokenVerifier
    rate_limiter: RateLimiter
    chat_service: ChatService
    table_service: TableService
    hub: ConnectionHub
    tickets: TicketStore
    character_service: CharacterService
    sheet_item_service: SheetItemService


def get_container(request: Request) -> Container:
    """Retourne le conteneur de services de l'application."""
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]


def _not_authenticated() -> AppError:
    return AppError(ErrorCode.NOT_AUTHENTICATED, "Authentification requise.", status_code=401)


@dataclass(frozen=True, slots=True)
class Session:
    """Session authentifiée d'une requête.

    Attributs:
        expires_at: expiration du jeton d'accès, en secondes depuis l'époque Unix.
    """

    account: Account
    expires_at: float


async def get_current_session(request: Request, container: ContainerDep) -> Session:
    """Identifie la session de la requête à partir du cookie de session.

    Le jeton est vérifié (signature, expiration, émetteur, audience) et le
    compte doit toujours exister et être actif.

    Raises:
        AppError: ``not_authenticated`` si la session est absente ou invalide.
    """
    token = request.cookies.get(ACCESS_COOKIE)
    if token is None:
        raise _not_authenticated()
    try:
        claims = await container.token_verifier.verify(token)
    except InvalidTokenError:
        raise _not_authenticated() from None
    account = await container.auth_service.get_active_account(claims.account_id)
    if account is None:
        raise _not_authenticated()
    return Session(account=account, expires_at=claims.expires_at)


CurrentSession = Annotated[Session, Depends(get_current_session)]


async def get_current_account(session: CurrentSession) -> Account:
    """Retourne le compte de la session en cours."""
    return session.account


CurrentAccount = Annotated[Account, Depends(get_current_account)]


async def require_gm(account: CurrentAccount) -> Account:
    """Réserve une route au MJ (CDC 8.3). Refus par défaut pour tout autre rôle."""
    if account.role is not Role.GM:
        raise AppError(ErrorCode.FORBIDDEN, "Action réservée au maître du jeu.", status_code=403)
    return account


CurrentGm = Annotated[Account, Depends(require_gm)]


def client_address(request: Request) -> str:
    """Adresse du client, en tenant compte du proxy placé devant le serveur."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(
    bucket: str, limit: int, window_seconds: float
) -> Callable[[Request, Container], Awaitable[None]]:
    """Fabrique une dépendance qui limite le débit par adresse cliente.

    Args:
        bucket: nom de l'opération limitée.
        limit: nombre maximal d'appels dans la fenêtre.
        window_seconds: durée de la fenêtre.
    """

    async def dependency(request: Request, container: ContainerDep) -> None:
        enforce_rate_limit(
            container.rate_limiter, f"{bucket}:ip:{client_address(request)}", limit, window_seconds
        )

    return dependency


def enforce_rate_limit(limiter: RateLimiter, key: str, limit: int, window_seconds: float) -> None:
    """Lève ``rate_limited`` (429) si la limite est atteinte pour cette clé."""
    if not limiter.allow(key, limit, window_seconds):
        raise AppError(
            ErrorCode.RATE_LIMITED, "Trop de tentatives. Réessaie dans un instant.", status_code=429
        )
