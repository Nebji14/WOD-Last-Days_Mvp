"""Routes de la connexion avec Google.

Le navigateur suit des redirections : départ vers Google, puis retour sur le
serveur qui ouvre la session et renvoie vers la table, ou vers la page de
connexion avec le code de l'erreur. Le même retour sert au profil, pour rattacher
un compte Google ou confirmer le titulaire.
"""

from typing import Literal
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse

from app.api.deps import Container, ContainerDep, rate_limit
from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.core.security import SessionTokens, set_session_cookies
from app.domain.accounts import Role
from app.services.google_auth import google_failed_error
from app.services.google_flow import GoogleFlow, GooglePurpose

router = APIRouter(prefix="/api/auth/google", tags=["auth"])

FLOW_COOKIE = "hunter_oauth"
_FLOW_COOKIE_PATH = "/api/auth/google"
# Temps laissé pour choisir son compte Google avant que le départ n'expire.
_FLOW_MAX_AGE_SECONDS = 600
_CALLBACK_PATH = "/api/auth/google/callback"
_TABLE_PATH = "/table"
_PLAYER_LOGIN_PATH = "/connexion"
_PROFILE_PATH = "/profil"
# Code de Supabase : ce compte Google appartient déjà à un autre compte.
_IDENTITY_EXISTS = "identity_already_exists"
_PROFILE_RESULTS = {GooglePurpose.LINK: "linked", GooglePurpose.CONFIRM: "confirmed"}
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
    set_flow_cookie(response, flow, container.settings)
    return response


@router.get(
    "/callback",
    dependencies=[Depends(rate_limit("google", _LIMIT_PER_ADDRESS, _WINDOW_SECONDS))],
)
async def callback(
    request: Request,
    container: ContainerDep,
    code: str | None = Query(default=None, max_length=512),
    error_code: str | None = Query(default=None, max_length=64),
) -> RedirectResponse:
    """Retour de Google : ouvre la session, ou renvoie l'erreur à la page de départ.

    Sans code (connexion annulée chez Google) ou sans cookie de départ, la
    connexion échoue.
    """
    settings = container.settings
    flow = GoogleFlow.decode(request.cookies.get(FLOW_COOKIE))
    try:
        if flow is not None and error_code == _IDENTITY_EXISTS:
            raise _already_linked_error()
        if flow is None or not code:
            raise google_failed_error()
        tokens = await _finish(container, code, flow)
        target = _success_url(flow)
    except AppError as error:
        response = RedirectResponse(_error_url(flow, error, settings), status_code=303)
    else:
        response = RedirectResponse(target, status_code=303)
        set_session_cookies(response, tokens, settings)
    response.delete_cookie(
        FLOW_COOKIE,
        path=_FLOW_COOKIE_PATH,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    return response


def set_flow_cookie(response: Response, flow: GoogleFlow, settings: Settings) -> None:
    """Mémorise le départ vers Google, relu au retour."""
    response.set_cookie(
        FLOW_COOKIE,
        flow.encode(),
        max_age=_FLOW_MAX_AGE_SECONDS,
        path=_FLOW_COOKIE_PATH,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


async def _finish(container: Container, code: str, flow: GoogleFlow) -> SessionTokens:
    """Termine l'aller-retour selon la raison du départ."""
    if flow.purpose is not GooglePurpose.LOGIN:
        return await container.google_link_service.finish(code, flow)
    _account, tokens = await container.google_auth_service.finish(code, flow)
    return tokens


def _already_linked_error() -> AppError:
    return AppError(
        ErrorCode.GOOGLE_ALREADY_LINKED,
        "Ce compte Google est déjà rattaché à un compte.",
        status_code=409,
    )


def _success_url(flow: GoogleFlow) -> str:
    """Page d'arrivée : la table après une connexion, sinon le profil."""
    result = _PROFILE_RESULTS.get(flow.purpose)
    return _TABLE_PATH if result is None else f"{_PROFILE_PATH}?{urlencode({'google': result})}"


def _error_url(flow: GoogleFlow | None, error: AppError, settings: Settings) -> str:
    """Page où afficher l'erreur : le profil s'il est à l'origine du départ."""
    if flow is not None and flow.purpose is not GooglePurpose.LOGIN:
        return f"{_PROFILE_PATH}?{urlencode({'google': error.code.value})}"
    return _login_url(flow.portal if flow is not None else Role.PLAYER, error, settings)


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
