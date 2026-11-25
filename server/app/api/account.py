"""Routes de gestion de son propre compte : noms, mot de passe, connexion Google."""

from fastapi import APIRouter, Request, Response, status

from app.api.deps import Container, ContainerDep, CurrentSession, Session, enforce_rate_limit
from app.api.google_auth import set_flow_cookie
from app.core.security import ACCESS_COOKIE, set_session_cookies
from app.schemas.account import (
    ChangePasswordRequest,
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


def _limit_confirmation(session: Session, container: Container) -> None:
    """Borne les essais de mot de passe actuel depuis une session ouverte."""
    enforce_rate_limit(
        container.rate_limiter,
        f"account:confirm:{session.account.id}",
        _CONFIRM_LIMIT_PER_ACCOUNT,
        _WINDOW_SECONDS,
    )
