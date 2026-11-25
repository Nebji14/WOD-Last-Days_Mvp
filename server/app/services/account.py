"""Cas d'usage de la gestion de son propre compte : noms et mot de passe."""

import logging
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.core.security import SessionTokens
from app.domain.accounts import Account, LoginMethods, is_valid_username, normalized_display_name
from app.gateways.supabase_auth import IdentityProviderError, InvalidCredentialsError
from app.repositories.accounts import UsernameAlreadyExistsError
from app.services.auth import ensure_password_allowed, unavailable_error, username_taken_error

logger = logging.getLogger(__name__)


class ProfileStore(Protocol):
    """Contrat d'accès aux comptes attendu par le service."""

    async def is_display_name_taken(self, display_name: str, account_id: UUID) -> bool: ...

    async def update_names(
        self, account_id: UUID, username: str | None, display_name: str | None
    ) -> Account: ...


class PasswordProvider(Protocol):
    """Contrat du fournisseur d'identité pour le changement de mot de passe."""

    async def set_password(
        self, user_id: UUID, password: str, email: str | None = None
    ) -> None: ...

    async def sign_in(self, email: str, password: str) -> SessionTokens: ...

    async def sign_out_others(self, access_token: str) -> None: ...


class OwnerConfirmation(Protocol):
    """Confirmation du titulaire avant une action sensible."""

    async def confirm(
        self, account: Account, password: str | None, authenticated_at: float | None
    ) -> LoginMethods: ...


class AccountRenamer(Protocol):
    """Met à jour le nom d'un participant autour de la table."""

    async def rename(self, account: Account) -> None: ...


class AccountBroadcaster(Protocol):
    """Diffusion en temps réel du nouveau nom d'un compte."""

    async def account_changed(self, account: Account) -> None: ...


class AccountService:
    """Orchestre la modification d'un compte par son titulaire, joueur ou MJ.

    Args:
        accounts: dépôt des comptes.
        identity: fournisseur d'identité.
        owner_check: confirmation du titulaire.
        table: état de la table, où le nom est affiché.
        broadcaster: diffusion en temps réel.
    """

    def __init__(
        self,
        accounts: ProfileStore,
        identity: PasswordProvider,
        owner_check: OwnerConfirmation,
        table: AccountRenamer,
        broadcaster: AccountBroadcaster,
    ) -> None:
        self._accounts = accounts
        self._identity = identity
        self._owner_check = owner_check
        self._table = table
        self._broadcaster = broadcaster

    async def update_names(
        self, account: Account, username: str | None, display_name: str | None
    ) -> Account:
        """Modifie le nom d'utilisateur et le nom affiché ; ``None`` conserve la valeur.

        Raises:
            AppError: ``username_invalid``, ``username_taken``,
                ``display_name_invalid`` ou ``display_name_taken``.
        """
        if username is not None and not is_valid_username(username):
            raise AppError(
                ErrorCode.USERNAME_INVALID, "Ce nom d'utilisateur n'est pas valide.", 422
            )
        new_display_name = await self._checked_display_name(account, display_name)
        try:
            updated = await self._accounts.update_names(account.id, username, new_display_name)
        except UsernameAlreadyExistsError:
            raise username_taken_error() from None
        if updated.display_name != account.display_name:
            await self._broadcaster.account_changed(updated)
            await self._table.rename(updated)
        return updated

    async def change_password(
        self,
        account: Account,
        *,
        current_password: str | None,
        password: str,
        password_confirmation: str,
        authenticated_at: float | None,
    ) -> SessionTokens:
        """Définit un nouveau mot de passe et ferme les autres sessions du compte.

        Un compte créé avec Google reçoit ainsi son premier mot de passe.

        Returns:
            Les jetons de la session rouverte avec le nouveau mot de passe.

        Raises:
            AppError: ``password_mismatch``, ``password_too_weak``,
                ``wrong_password``, ``reauthentication_required`` ou
                ``service_unavailable``.
        """
        ensure_password_allowed(password, password_confirmation)
        methods = await self._owner_check.confirm(account, current_password, authenticated_at)
        # L'adresse accompagne le premier mot de passe : elle crée la méthode de
        # connexion par mot de passe à côté de Google.
        first_password_email = None if methods.password else account.auth_email
        try:
            await self._identity.set_password(account.id, password, first_password_email)
            tokens = await self._identity.sign_in(account.auth_email, password)
        except (IdentityProviderError, InvalidCredentialsError):
            raise unavailable_error() from None
        try:
            await self._identity.sign_out_others(tokens.access_token)
        except IdentityProviderError:
            logger.warning("Autres sessions non révoquées après un changement de mot de passe")
        return tokens

    async def _checked_display_name(self, account: Account, display_name: str | None) -> str | None:
        """Contrôle le nom affiché ; deux participants ne portent pas le même."""
        if display_name is None:
            return None
        normalized = normalized_display_name(display_name)
        if normalized is None:
            raise AppError(ErrorCode.DISPLAY_NAME_INVALID, "Ce nom affiché n'est pas valide.", 422)
        changed = normalized.casefold() != account.display_name.casefold()
        if changed and await self._accounts.is_display_name_taken(normalized, account.id):
            raise AppError(
                ErrorCode.DISPLAY_NAME_TAKEN, "Ce nom affiché est déjà pris.", status_code=409
            )
        return normalized
