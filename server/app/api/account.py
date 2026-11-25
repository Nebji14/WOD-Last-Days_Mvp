"""Routes de gestion de son propre compte.

Noms, mot de passe, connexion Google, photo du MJ et départ d'un joueur.
"""

from fastapi import APIRouter, Request, Response, status

from app.api.deps import (
    Container,
    ContainerDep,
    CurrentGm,
    CurrentSession,
    Session,
    enforce_rate_limit,
)
from app.api.google_auth import set_flow_cookie
from app.api.portraits import limit_portrait_uploads
from app.api.uploads import read_body
from app.core.security import ACCESS_COOKIE, clear_session_cookies, set_session_cookies
from app.domain.portraits import MAX_PORTRAIT_BYTES
from app.schemas.account import (
    ChangePasswordRequest,
    CloseAccountRequest,
    GoogleUrlResponse,
    OwnerConfirmationRequest,
    UpdateAccountRequest,
)
from app.schemas.auth import AccountResponse

router = APIRouter(prefix="/api/account", tags=["account"])

_WINDOW_SECONDS = 600.0
_EDIT_LIMIT_PER_ACCOUNT = 30
# Partagée par toutes les actions qui vérifient le mot de passe actuel.
_CONFIRM_LIMIT_PER_ACCOUNT = 8


@router.patch("")
async def update_account(
    payload: UpdateAccountRequest, session: CurrentSession, container: ContainerDep
) -> AccountResponse:
    """Modifie le nom d'utilisateur et le nom affiché."""
    enforce_rate_limit(
        container.rate_limiter,
        f"account:edit:{session.account.id}",
        _EDIT_LIMIT_PER_ACCOUNT,
        _WINDOW_SECONDS,
    )
    account = await container.account_service.update_names(
        session.account, payload.username, payload.display_name
    )
    return AccountResponse.from_account(account)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest, session: CurrentSession, container: ContainerDep
) -> Response:
    """Change le mot de passe, ou définit le premier, et renouvelle la session."""
    _limit_confirmation(session, container)
    tokens = await container.account_service.change_password(
        session.account,
        current_password=payload.current_password,
        password=payload.password,
        password_confirmation=payload.password_confirmation,
        authenticated_at=session.authenticated_at,
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    set_session_cookies(response, tokens, container.settings)
    return response


@router.put("/portrait")
async def replace_portrait(
    request: Request, gm: CurrentGm, container: ContainerDep
) -> AccountResponse:
    """Donne une photo au MJ ; le fichier est envoyé tel quel."""
    limit_portrait_uploads(container, gm)
    content = await read_body(request, MAX_PORTRAIT_BYTES)
    account = await container.account_portrait_service.replace(gm, content)
    return AccountResponse.from_account(account)


@router.delete("/portrait")
async def remove_portrait(gm: CurrentGm, container: ContainerDep) -> AccountResponse:
    """Retire la photo du MJ."""
    account = await container.account_portrait_service.remove(gm)
    return AccountResponse.from_account(account)


@router.post("/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_account(
    payload: CloseAccountRequest,
    request: Request,
    session: CurrentSession,
    container: ContainerDep,
) -> Response:
    """Désactive le compte du joueur : ses données restent, le MJ peut lui rendre l'accès."""
    _limit_confirmation(session, container)
    await container.account_closure_service.disable(
        session.account,
        username=payload.username,
        password=payload.current_password,
        authenticated_at=session.authenticated_at,
        access_token=request.cookies[ACCESS_COOKIE],
    )
    return _signed_out(container)


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    payload: CloseAccountRequest, session: CurrentSession, container: ContainerDep
) -> Response:
    """Supprime définitivement le compte du joueur et toutes ses données."""
    _limit_confirmation(session, container)
    await container.account_closure_service.delete(
        session.account,
        username=payload.username,
        password=payload.current_password,
        authenticated_at=session.authenticated_at,
    )
    return _signed_out(container)


@router.post("/google/link")
async def link_google(
    payload: OwnerConfirmationRequest,
    request: Request,
    response: Response,
    session: CurrentSession,
    container: ContainerDep,
) -> GoogleUrlResponse:
    """Prépare le départ vers Google pour rattacher ou remplacer un compte Google."""
    _limit_confirmation(session, container)
    url, flow = await container.google_link_service.start_link(
        session.account,
        request.cookies[ACCESS_COOKIE],
        payload.current_password,
        session.authenticated_at,
    )
    set_flow_cookie(response, flow, container.settings)
    return GoogleUrlResponse(url=url)


@router.post("/google/confirm")
async def confirm_with_google(
    response: Response, session: CurrentSession, container: ContainerDep
) -> GoogleUrlResponse:
    """Prépare une reconnexion Google, demandée à un compte sans mot de passe."""
    _limit_confirmation(session, container)
    url, flow = container.google_link_service.start_confirm(session.account)
    set_flow_cookie(response, flow, container.settings)
    return GoogleUrlResponse(url=url)


@router.post("/google/unlink", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_google(
    payload: OwnerConfirmationRequest,
    request: Request,
    session: CurrentSession,
    container: ContainerDep,
) -> None:
    """Retire la connexion Google, si le compte garde un mot de passe."""
    _limit_confirmation(session, container)
    await container.google_link_service.unlink(
        session.account,
        request.cookies[ACCESS_COOKIE],
        payload.current_password,
        session.authenticated_at,
    )


def _signed_out(container: Container) -> Response:
    """Réponse vide qui retire les cookies de session."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookies(response, container.settings)
    return response


def _limit_confirmation(session: Session, container: Container) -> None:
    """Borne les essais de mot de passe actuel depuis une session ouverte."""
    enforce_rate_limit(
        container.rate_limiter,
        f"account:confirm:{session.account.id}",
        _CONFIRM_LIMIT_PER_ACCOUNT,
        _WINDOW_SECONDS,
    )
