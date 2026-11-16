"""Routes d'authentification (US-001, US-002, US-003, US-023).

Les routes ne contiennent aucune logique métier : elles valident l'entrée,
appellent le service et gèrent les cookies de session.
"""

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import ContainerDep, CurrentAccount, enforce_rate_limit, rate_limit
from app.core.errors import AppError, ErrorCode
from app.core.security import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    clear_session_cookies,
    set_session_cookies,
)
from app.domain.accounts import Role
from app.schemas.auth import AccountResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])

_WINDOW_SECONDS = 600.0
_REGISTER_LIMIT_PER_ADDRESS = 5
_LOGIN_LIMIT_PER_ADDRESS = 20
_LOGIN_LIMIT_PER_USERNAME = 8
_REFRESH_LIMIT_PER_ADDRESS = 120


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", _REGISTER_LIMIT_PER_ADDRESS, _WINDOW_SECONDS))],
)
async def register(payload: RegisterRequest, container: ContainerDep) -> AccountResponse:
    """Crée un compte joueur. N'ouvre pas de session (02b-C3)."""
    account = await container.auth_service.register_player(
        payload.username, payload.password, payload.password_confirmation
    )
    return AccountResponse.from_account(account)


@router.post(
    "/login",
    dependencies=[Depends(rate_limit("login", _LOGIN_LIMIT_PER_ADDRESS, _WINDOW_SECONDS))],
)
async def login_player(
    payload: LoginRequest, response: Response, container: ContainerDep
) -> AccountResponse:
    """Connexion depuis l'accès joueur (02a)."""
    return await _login(payload, response, container, Role.PLAYER)


@router.post(
    "/gm/login",
    dependencies=[Depends(rate_limit("login", _LOGIN_LIMIT_PER_ADDRESS, _WINDOW_SECONDS))],
)
async def login_gm(
    payload: LoginRequest, response: Response, container: ContainerDep
) -> AccountResponse:
    """Connexion depuis l'accès dédié du MJ (02c)."""
    return await _login(payload, response, container, Role.GM)


@router.post(
    "/refresh",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("refresh", _REFRESH_LIMIT_PER_ADDRESS, _WINDOW_SECONDS))],
)
async def refresh(request: Request, container: ContainerDep) -> Response:
    """Renouvelle la session à partir du cookie de rafraîchissement."""
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    if refresh_token is None:
        raise AppError(ErrorCode.NOT_AUTHENTICATED, "La session a expiré.", status_code=401)
    tokens = await container.auth_service.refresh(refresh_token)
    set_session_cookies(response, tokens, container.settings)
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, container: ContainerDep) -> Response:
    """Ferme la session et retire les cookies (US-003)."""
    await container.auth_service.logout(request.cookies.get(ACCESS_COOKIE))
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookies(response, container.settings)
    return response


@router.get("/me")
async def me(account: CurrentAccount) -> AccountResponse:
    """Retourne le compte de la session en cours."""
    return AccountResponse.from_account(account)


async def _login(
    payload: LoginRequest, response: Response, container: ContainerDep, portal: Role
) -> AccountResponse:
    """Limite les essais par nom d'utilisateur, ouvre la session et dépose les cookies."""
    enforce_rate_limit(
        container.rate_limiter,
        f"login:user:{payload.username.lower()}",
        _LOGIN_LIMIT_PER_USERNAME,
        _WINDOW_SECONDS,
    )
    account, tokens = await container.auth_service.login(payload.username, payload.password, portal)
    set_session_cookies(response, tokens, container.settings)
    return AccountResponse.from_account(account)
