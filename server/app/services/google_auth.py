"""Connexion et inscription avec Google, par le flux OAuth PKCE de Supabase.

Le serveur mène tout l'échange : le navigateur ne voit jamais les jetons, qui
finissent dans les cookies de session comme pour une connexion par mot de passe.
Un compte Google inconnu devient un compte joueur, avec un nom d'utilisateur
tiré du nom Google.
"""

import logging
from typing import Protocol

from app.core.errors import AppError, ErrorCode
from app.core.security import SessionTokens, pkce_challenge
from app.domain.accounts import Account, Role, numbered_username, username_from_identity
from app.gateways.supabase_auth import (
    ExternalIdentity,
    IdentityProviderError,
    InvalidCredentialsError,
)
from app.repositories.accounts import UsernameAlreadyExistsError
from app.services.auth import AccountStore, unavailable_error, wrong_portal_error
from app.services.google_flow import GoogleFlow

logger = logging.getLogger(__name__)

GOOGLE_PROVIDER = "google"
# Essais de noms numérotés (« lea », « lea2 »…) avant d'abandonner.
_MAX_USERNAME_ATTEMPTS = 50


class ExternalIdentityProvider(Protocol):
    """Contrat du fournisseur d'identité pour une connexion externe."""

    def authorize_url(self, provider: str, redirect_to: str, code_challenge: str) -> str: ...

    async def exchange_code(self, auth_code: str, code_verifier: str) -> SessionTokens: ...

    async def get_user(self, access_token: str) -> ExternalIdentity: ...

    async def sign_out(self, access_token: str) -> None: ...


def google_failed_error() -> AppError:
    """La connexion avec Google a été annulée, a expiré ou a été refusée."""
    return AppError(
        ErrorCode.GOOGLE_FAILED, "La connexion avec Google n'a pas abouti.", status_code=401
    )


class GoogleAuthService:
    """Orchestre la connexion Google.

    Args:
        accounts: dépôt des comptes.
        identity: fournisseur d'identité.
        redirect_url: adresse de retour après Google, déclarée dans Supabase.
        gm_access_path: chemin de la page du MJ, renvoyé quand il se trompe de page.
    """

    def __init__(
        self,
        accounts: AccountStore,
        identity: ExternalIdentityProvider,
        redirect_url: str,
        gm_access_path: str = "",
    ) -> None:
        self._accounts = accounts
        self._identity = identity
        self._redirect_url = redirect_url
        self._gm_access_path = gm_access_path

    def start(self, portal: Role) -> tuple[str, GoogleFlow]:
        """Prépare le départ vers Google : adresse à ouvrir et flux à mémoriser."""
        flow = GoogleFlow.new(portal)
        url = self._identity.authorize_url(
            GOOGLE_PROVIDER, self._redirect_url, pkce_challenge(flow.verifier)
        )
        return url, flow

    async def finish(self, code: str, flow: GoogleFlow) -> tuple[Account, SessionTokens]:
        """Termine la connexion au retour de Google.

        Sur la page des joueurs, un compte Google inconnu est créé comme compte
        joueur. Sur la page du MJ, aucun compte n'est créé.

        Raises:
            AppError: ``google_failed``, ``invalid_credentials`` (compte
                désactivé), ``wrong_portal_gm``, ``wrong_portal_player`` ou
                ``service_unavailable``.
        """
        try:
            tokens = await self._identity.exchange_code(code, flow.verifier)
        except InvalidCredentialsError:
            raise google_failed_error() from None
        except IdentityProviderError:
            raise unavailable_error() from None
        try:
            account = await self._account_for(tokens, flow.portal)
        except AppError:
            await self._discard_session(tokens)
            raise
        return account, tokens

    async def _account_for(self, tokens: SessionTokens, portal: Role) -> Account:
        """Retrouve ou crée le compte de l'utilisateur Google, puis contrôle la page."""
        try:
            identity = await self._identity.get_user(tokens.access_token)
        except IdentityProviderError:
            raise unavailable_error() from None
        account = await self._accounts.get_by_id(identity.user_id)
        if account is None:
            if portal is Role.GM:
                raise wrong_portal_error(Role.PLAYER, self._gm_access_path)
            account = await self._create_player(identity)
        if not account.is_active:
            raise AppError(
                ErrorCode.INVALID_CREDENTIALS, "Identifiant ou mot de passe incorrect.", 401
            )
        if account.role is not portal:
            raise wrong_portal_error(account.role, self._gm_access_path)
        return account

    async def _create_player(self, identity: ExternalIdentity) -> Account:
        """Crée le compte joueur avec le premier nom d'utilisateur libre."""
        base = username_from_identity(identity.full_name, identity.email)
        for number in range(1, _MAX_USERNAME_ATTEMPTS + 1):
            username = numbered_username(base, number)
            if await self._accounts.get_by_username(username) is not None:
                continue
            try:
                return await self._accounts.create(
                    account_id=identity.user_id,
                    username=username,
                    display_name=username,
                    auth_email=identity.email.lower(),
                    role=Role.PLAYER,
                )
            except UsernameAlreadyExistsError:
                # Une connexion simultanée du même utilisateur a pu créer le compte.
                existing = await self._accounts.get_by_id(identity.user_id)
                if existing is not None:
                    return existing
        logger.error("Aucun nom d'utilisateur libre pour un compte Google")
        raise unavailable_error()

    async def _discard_session(self, tokens: SessionTokens) -> None:
        """Révoque la session ouverte par Google quand la connexion est refusée."""
        try:
            await self._identity.sign_out(tokens.access_token)
        except IdentityProviderError:
            logger.warning("Session Google refusée non révoquée")
