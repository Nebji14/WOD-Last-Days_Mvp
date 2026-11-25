"""Connexion Google d'un compte déjà ouvert : rattacher, remplacer, retirer, confirmer.

Le nouveau compte Google est rattaché avant de retirer l'ancien : le titulaire
garde toujours au moins une méthode de connexion utilisable.
"""

import logging
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.core.security import SessionTokens, pkce_challenge
from app.domain.accounts import Account
from app.gateways.supabase_auth import (
    ExternalIdentity,
    IdentityProviderError,
    InvalidCredentialsError,
    LinkedIdentity,
)
from app.services.account import OwnerConfirmation
from app.services.auth import unavailable_error
from app.services.google_auth import GOOGLE_PROVIDER, google_failed_error
from app.services.google_flow import GoogleFlow, GooglePurpose

logger = logging.getLogger(__name__)


class LinkedAccountStore(Protocol):
    """Contrat d'accès aux comptes attendu par le service."""

    async def get_by_id(self, account_id: UUID) -> Account | None: ...

    async def update_auth_email(self, account_id: UUID, auth_email: str) -> None: ...


class LinkingProvider(Protocol):
    """Contrat du fournisseur d'identité pour les connexions externes."""

    def authorize_url(self, provider: str, redirect_to: str, code_challenge: str) -> str: ...

    async def link_url(
        self, access_token: str, provider: str, redirect_to: str, code_challenge: str
    ) -> str: ...

    async def exchange_code(self, auth_code: str, code_verifier: str) -> SessionTokens: ...

    async def get_user(self, access_token: str) -> ExternalIdentity: ...

    async def linked_identities(self, access_token: str) -> list[LinkedIdentity]: ...

    async def unlink_identity(self, access_token: str, identity_id: UUID) -> None: ...

    async def delete_user(self, user_id: UUID) -> None: ...

    async def sign_out(self, access_token: str) -> None: ...


class GoogleLinkService:
    """Orchestre la connexion Google d'un compte connecté.

    Args:
        accounts: dépôt des comptes.
        identity: fournisseur d'identité.
        owner_check: confirmation du titulaire.
        redirect_url: adresse de retour après Google, déclarée dans Supabase.
    """

    def __init__(
        self,
        accounts: LinkedAccountStore,
        identity: LinkingProvider,
        owner_check: OwnerConfirmation,
        redirect_url: str,
    ) -> None:
        self._accounts = accounts
        self._identity = identity
        self._owner_check = owner_check
        self._redirect_url = redirect_url

    async def start_link(
        self,
        account: Account,
        access_token: str,
        password: str | None,
        authenticated_at: float | None,
    ) -> tuple[str, GoogleFlow]:
        """Prépare le rattachement d'un compte Google, qui remplacera l'éventuel ancien.

        Raises:
            AppError: ``wrong_password``, ``reauthentication_required`` ou
                ``service_unavailable``.
        """
        await self._owner_check.confirm(account, password, authenticated_at)
        flow = GoogleFlow.new(account.role, GooglePurpose.LINK, account.id)
        try:
            url = await self._identity.link_url(
                access_token, GOOGLE_PROVIDER, self._redirect_url, pkce_challenge(flow.verifier)
            )
        except IdentityProviderError:
            raise unavailable_error() from None
        return url, flow

    def start_confirm(self, account: Account) -> tuple[str, GoogleFlow]:
        """Prépare une reconnexion Google, qui confirme un titulaire sans mot de passe."""
        flow = GoogleFlow.new(account.role, GooglePurpose.CONFIRM, account.id)
        url = self._identity.authorize_url(
            GOOGLE_PROVIDER, self._redirect_url, pkce_challenge(flow.verifier)
        )
        return url, flow

    async def finish(self, code: str, flow: GoogleFlow) -> SessionTokens:
        """Termine un rattachement ou une confirmation au retour de Google.

        Raises:
            AppError: ``google_failed`` ou ``service_unavailable``.
        """
        try:
            tokens = await self._identity.exchange_code(code, flow.verifier)
            identity = await self._identity.get_user(tokens.access_token)
        except InvalidCredentialsError:
            raise google_failed_error() from None
        except IdentityProviderError:
            raise unavailable_error() from None
        account = await self._accounts.get_by_id(identity.user_id)
        if account is None or not account.is_active or account.id != flow.account_id:
            await self._reject(tokens, identity, known=account is not None)
            raise google_failed_error()
        if flow.purpose is GooglePurpose.LINK:
            await self._drop_previous(account, tokens.access_token)
        return tokens

    async def unlink(
        self,
        account: Account,
        access_token: str,
        password: str | None,
        authenticated_at: float | None,
    ) -> None:
        """Retire la connexion Google d'un compte qui garde un mot de passe.

        Raises:
            AppError: ``last_login_method``, ``wrong_password``,
                ``reauthentication_required`` ou ``service_unavailable``.
        """
        methods = await self._owner_check.confirm(account, password, authenticated_at)
        if not methods.password:
            raise AppError(
                ErrorCode.LAST_LOGIN_METHOD,
                "Le compte doit garder au moins une méthode de connexion.",
                status_code=409,
            )
        try:
            for linked in await self._google_identities(access_token):
                await self._identity.unlink_identity(access_token, linked.identity_id)
        except IdentityProviderError:
            raise unavailable_error() from None
        await self._sync_email(account, access_token)

    async def _drop_previous(self, account: Account, access_token: str) -> None:
        """Retire les anciens comptes Google ; un échec les laisse simplement utilisables."""
        try:
            for linked in (await self._google_identities(access_token))[:-1]:
                await self._identity.unlink_identity(access_token, linked.identity_id)
        except IdentityProviderError:
            logger.warning("Ancien compte Google non retiré")
        await self._sync_email(account, access_token)

    async def _google_identities(self, access_token: str) -> list[LinkedIdentity]:
        """Comptes Google rattachés, du plus ancien au plus récent."""
        identities = await self._identity.linked_identities(access_token)
        google = [linked for linked in identities if linked.provider == GOOGLE_PROVIDER]
        return sorted(google, key=lambda linked: linked.created_at)

    async def _sync_email(self, account: Account, access_token: str) -> None:
        """Recopie l'adresse de connexion, qui peut changer quand un compte Google est retiré."""
        try:
            identity = await self._identity.get_user(access_token)
        except IdentityProviderError:
            logger.error("Adresse de connexion non relue après un changement de compte Google")
            return
        email = identity.email.lower()
        if email != account.auth_email:
            await self._accounts.update_auth_email(account.id, email)

    async def _reject(
        self, tokens: SessionTokens, identity: ExternalIdentity, *, known: bool
    ) -> None:
        """Ferme la session d'un autre compte Google, et l'oublie s'il n'a pas de compte ici."""
        try:
            await self._identity.sign_out(tokens.access_token)
            if not known:
                await self._identity.delete_user(identity.user_id)
        except IdentityProviderError:
            logger.warning("Session Google refusée non révoquée")
