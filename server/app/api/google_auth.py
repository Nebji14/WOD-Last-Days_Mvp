"""Routes de la connexion avec Google.

Le navigateur suit des redirections : départ vers Google, puis retour sur le
serveur qui ouvre la session et renvoie vers la table, ou vers la page de
connexion avec le code de l'erreur.
"""

from typing import Literal
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse

from app.api.deps import ContainerDep, rate_limit
from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.core.security import set_session_cookies
from app.domain.accounts import Role
from app.services.google_auth import GoogleFlow, google_failed_error

router = APIRouter(prefix="/api/auth/google", tags=["auth"])

FLOW_COOKIE = "hunter_oauth"
_FLOW_COOKIE_PATH = "/api/auth/google"
# Temps laissé pour choisir son compte Google avant que le départ n'expire.
_FLOW_MAX_AGE_SECONDS = 600
_CALLBACK_PATH = "/api/auth/google/callback"
_TABLE_PATH = "/table"
_PLAYER_LOGIN_PATH = "/connexion"
_WINDOW_SECONDS = 600.0
_LIMIT_PER_ADDRESS = 30


def google_callback_url(settings: Settings) -> str:
    """Adresse de retour après Google, à déclarer dans les Redirect URLs de Supabase."""
    return f"{settings.public_app_url}{_CALLBACK_PATH}"


@router.get(
    "/start",
    dependencies=[Depends(rate_limit("google", _LIMIT_PER_ADDRESS, _WINDOW_SECONDS))],
)
async def start(
    container: ContainerDep, portal: Literal["player", "gm"] = "player"
) -> RedirectResponse:
    """Envoie le navigateur vers Google et mémorise le secret PKCE dans un cookie."""
    url, flow = container.google_auth_service.start(Role(portal))
    response = RedirectResponse(url, status_code=303)
    response.set_cookie(
        FLOW_COOKIE,
        flow.encode(),
        max_age=_FLOW_MAX_AGE_SECONDS,
        path=_FLOW_COOKIE_PATH,
        httponly=True,
        secure=container.settings.is_production,
        samesite="lax",
    )
    return response


@router.get(
    "/callback",
    dependencies=[Depends(rate_limit("google", _LIMIT_PER_ADDRESS, _WINDOW_SECONDS))],
)
async def callback(
    request: Request,
    container: ContainerDep,
    code: str | None = Query(default=None, max_length=512),
) -> RedirectResponse:
    """Retour de Google : ouvre la session, ou renvoie l'erreur à la page de départ.

    Sans code (connexion annulée chez Google) ou sans cookie de départ, la
    connexion échoue.
    """
    settings = container.settings
    flow = GoogleFlow.decode(request.cookies.get(FLOW_COOKIE))
    portal = flow.portal if flow is not None else Role.PLAYER
    try:
        if flow is None or not code:
            raise google_failed_error()
        _account, tokens = await container.google_auth_service.finish(code, flow)
    except AppError as error:
        response = RedirectResponse(_login_url(portal, error, settings), status_code=303)
    else:
        response = RedirectResponse(_TABLE_PATH, status_code=303)
        set_session_cookies(response, tokens, settings)
    response.delete_cookie(
        FLOW_COOKIE,
        path=_FLOW_COOKIE_PATH,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    return response


def _login_url(portal: Role, error: AppError, settings: Settings) -> str:
    """Page de connexion de départ, avec le code d'erreur à afficher.

    Pour le MJ qui s'est trompé de page, le lien vers sa page accompagne l'erreur.
    """
    gm_path = settings.gm_access_path
    base = f"/{gm_path}/connexion" if portal is Role.GM and gm_path else _PLAYER_LOGIN_PATH
    query = {"erreur": error.code.value}
    if error.code is ErrorCode.WRONG_PORTAL_GM and gm_path:
        query["acces"] = f"/{gm_path}"
    return f"{base}?{urlencode(query)}"
