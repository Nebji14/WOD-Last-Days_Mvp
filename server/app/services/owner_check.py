"""Vérifie que la personne devant l'écran est bien le titulaire du compte.

Une session ouverte ne suffit pas pour une action sensible : un compte avec mot
de passe le ressaisit, un compte Google doit s'être connecté à l'instant.
"""

import logging
import time
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.core.security import SessionTokens
from app.domain.accounts import Account, LoginMethods
from app.gateways.supabase_auth import IdentityProviderError, InvalidCredentialsError
from app.services.auth import unavailable_error

logger = logging.getLogger(__name__)

RECENT_LOGIN_SECONDS = 600.0


class LoginMethodStore(Protocol):
    """Accès aux méthodes de connexion d'un compte."""

    async def login_methods(self, account_id: UUID) -> LoginMethods: ...


class PasswordVerifier(Protocol):
    """Vérification d'un mot de passe auprès du fournisseur d'identité."""

    async def sign_in(self, email: str, password: str) -> SessionTokens: ...

    async def sign_out(self, access_token: str) -> None: ...


class OwnerCheck:
    """Confirme l'identité du titulaire avant une action sensible.

    Args:
        methods: méthodes de connexion des comptes.
        identity: fournisseur d'identité.
    """

    def __init__(self, methods: LoginMethodStore, identity: PasswordVerifier) -> None:
        self._methods = methods
        self._identity = identity

    async def confirm(
        self, account: Account, password: str | None, authenticated_at: float | None
    ) -> LoginMethods:
        """Retourne les méthodes de connexion du compte une fois le titulaire confirmé.

        Args:
            password: mot de passe ressaisi, si le compte en a un.
            authenticated_at: date de la dernière connexion de la session.

        Raises:
            AppError: ``wrong_password``, ``reauthentication_required`` ou
                ``service_unavailable``.
        """
        methods = await self._methods.login_methods(account.id)
        if methods.password:
            await self._check_password(account, password)
        elif authenticated_at is None or time.time() - authenticated_at > RECENT_LOGIN_SECONDS:
            raise AppError(
                ErrorCode.REAUTHENTICATION_REQUIRED,
                "Une connexion récente est demandée pour cette action.",
                status_code=403,
            )
        return methods

    async def _check_password(self, account: Account, password: str | None) -> None:
        """Compare le mot de passe ressaisi, puis referme la session ouverte pour l'essai."""
        try:
            tokens = await self._identity.sign_in(account.auth_email, password or "")
        except InvalidCredentialsError:
            raise AppError(
                ErrorCode.WRONG_PASSWORD, "Le mot de passe actuel est incorrect.", status_code=403
            ) from None
        except IdentityProviderError:
            raise unavailable_error() from None
        try:
            await self._identity.sign_out(tokens.access_token)
        except IdentityProviderError:
            logger.warning("Session de vérification non révoquée")
