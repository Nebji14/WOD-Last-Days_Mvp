"""Cas d'usage d'authentification : inscription, connexion, session.

Inscription des joueurs, connexion (joueur ou MJ par sa page dédiée),
renouvellement et fermeture de la session.
"""

import logging
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.core.security import SessionTokens
from app.domain.accounts import (
    Account,
    Role,
    is_valid_username,
    password_violations,
    technical_email,
)
from app.gateways.supabase_auth import (
    IdentityAlreadyExistsError,
    IdentityProviderError,
    InvalidCredentialsError,
)
from app.repositories.accounts import UsernameAlreadyExistsError

logger = logging.getLogger(__name__)


class AccountStore(Protocol):
    """Contrat d'accès aux comptes attendu par le service."""

    async def get_by_id(self, account_id: UUID) -> Account | None: ...

    async def get_by_username(self, username: str) -> Account | None: ...

    async def create(
        self, *, account_id: UUID, username: str, display_name: str, auth_email: str, role: Role
    ) -> Account: ...


class IdentityProvider(Protocol):
    """Contrat du fournisseur d'identité attendu par le service."""

    async def create_user(self, email: str, password: str) -> UUID: ...

    async def delete_user(self, user_id: UUID) -> None: ...

    async def sign_in(self, email: str, password: str) -> SessionTokens: ...

    async def refresh(self, refresh_token: str) -> SessionTokens: ...

    async def sign_out(self, access_token: str) -> None: ...

    async def get_providers(self, user_id: UUID) -> list[str]: ...


def _invalid_credentials() -> AppError:
    """Erreur unique pour tout échec de connexion : aucune énumération des comptes."""
    return AppError(
        ErrorCode.INVALID_CREDENTIALS, "Identifiant ou mot de passe incorrect.", status_code=401
    )


def _username_taken() -> AppError:
    return AppError(
        ErrorCode.USERNAME_TAKEN, "Ce nom d'utilisateur est déjà pris.", status_code=409
    )


def unavailable_error() -> AppError:
    """Erreur renvoyée quand le fournisseur d'identité ne répond pas."""
    return AppError(
        ErrorCode.SERVICE_UNAVAILABLE,
        "Le service d'authentification est momentanément indisponible.",
        status_code=503,
    )


def wrong_portal_error(account_role: Role, gm_access_path: str) -> AppError:
    """Compte valide présenté sur la mauvaise page de connexion.

    Le chemin de la page du MJ n'est donné qu'au MJ lui-même.
    """
    if account_role is Role.GM:
        return AppError(
            ErrorCode.WRONG_PORTAL_GM,
            "Ce compte se connecte par l'accès du MJ.",
            403,
            details=[{"gm_access_path": f"/{gm_access_path}"}] if gm_access_path else None,
        )
    return AppError(ErrorCode.WRONG_PORTAL_PLAYER, "Cet accès est réservé au maître du jeu.", 403)


class AuthService:
    """Orchestre les comptes et le fournisseur d'identité.

    Args:
        accounts: dépôt des comptes.
        identity: fournisseur d'identité.
        technical_email_domain: domaine des adresses techniques des joueurs.
        gm_access_path: chemin de la page du MJ, renvoyé quand il se trompe de page.
    """

    def __init__(
        self,
        accounts: AccountStore,
        identity: IdentityProvider,
        technical_email_domain: str,
        gm_access_path: str = "",
    ) -> None:
        self._accounts = accounts
        self._identity = identity
        self._email_domain = technical_email_domain
        self._gm_access_path = gm_access_path

    async def register_player(
        self, username: str, password: str, password_confirmation: str
    ) -> Account:
        """Crée un compte joueur après contrôle du nom et du mot de passe.

        Le joueur n'est pas connecté à l'issue de l'inscription.

        Raises:
            AppError: ``username_invalid``, ``password_mismatch``,
                ``password_too_weak`` ou ``username_taken``.
        """
        if not is_valid_username(username):
            raise AppError(
                ErrorCode.USERNAME_INVALID, "Ce nom d'utilisateur n'est pas valide.", 422
            )
        if password != password_confirmation:
            raise AppError(
                ErrorCode.PASSWORD_MISMATCH, "Les deux mots de passe sont différents.", 422
            )
        violations = password_violations(password)
        if violations:
            raise AppError(
                ErrorCode.PASSWORD_TOO_WEAK,
                "Le mot de passe ne respecte pas les règles de sécurité.",
                422,
                details=[{"rule": rule.value} for rule in violations],
            )
        if await self._accounts.get_by_username(username) is not None:
            raise _username_taken()
        return await self._create_account(
            username=username,
            password=password,
            auth_email=technical_email(username, self._email_domain),
            role=Role.PLAYER,
        )

    async def create_gm(self, username: str, email: str, password: str) -> Account:
        """Crée le compte MJ, depuis le script d'initialisation uniquement.

        L'adresse est réelle : elle sert à la récupération du mot de passe.

        Raises:
            AppError: si les données sont invalides ou si un compte MJ existe déjà.
        """
        if not is_valid_username(username):
            raise AppError(ErrorCode.USERNAME_INVALID, "Identifiant du MJ invalide.", 422)
        violations = password_violations(password)
        if violations:
            raise AppError(
                ErrorCode.PASSWORD_TOO_WEAK,
                "Le mot de passe ne respecte pas les règles de sécurité.",
                422,
                details=[{"rule": rule.value} for rule in violations],
            )
        return await self._create_account(
            username=username, password=password, auth_email=email.lower(), role=Role.GM
        )

    async def login(
        self, username: str, password: str, portal: Role
    ) -> tuple[Account, SessionTokens]:
        """Ouvre une session depuis la page des joueurs ou celle du MJ.

        Des identifiants valides saisis sur le mauvais accès n'ouvrent pas de
        session et produisent une erreur dédiée.

        Raises:
            AppError: ``invalid_credentials``, ``wrong_portal_gm`` (compte MJ sur
                l'accès joueur) ou ``wrong_portal_player`` (compte joueur sur
                l'accès MJ).
        """
        account = await self._accounts.get_by_username(username)
        if account is None or not account.is_active:
            await self._equalize_timing(password)
            raise _invalid_credentials()
        try:
            tokens = await self._identity.sign_in(account.auth_email, password)
        except InvalidCredentialsError:
            raise _invalid_credentials() from None
        except IdentityProviderError:
            raise unavailable_error() from None

        if account.role is not portal:
            await self._discard_session(tokens)
            raise wrong_portal_error(account.role, self._gm_access_path)
        return account, tokens

    async def refresh(self, refresh_token: str) -> SessionTokens:
        """Renouvelle la session.

        Raises:
            AppError: ``not_authenticated`` si le jeton est refusé.
        """
        try:
            return await self._identity.refresh(refresh_token)
        except InvalidCredentialsError:
            raise AppError(
                ErrorCode.NOT_AUTHENTICATED, "La session a expiré.", status_code=401
            ) from None
        except IdentityProviderError:
            raise unavailable_error() from None

    async def logout(self, access_token: str | None) -> None:
        """Ferme la session. N'échoue jamais : les cookies sont supprimés par la route."""
        if access_token is None:
            return
        try:
            await self._identity.sign_out(access_token)
        except IdentityProviderError:
            logger.warning(
                "Révocation de session impossible ; les cookies sont tout de même retirés"
            )

    async def login_methods(self, account_id: UUID) -> list[str]:
        """Méthodes de connexion du compte : ``password`` et/ou ``google``.

        Raises:
            AppError: ``service_unavailable`` si le fournisseur ne répond pas.
        """
        try:
            providers = await self._identity.get_providers(account_id)
        except IdentityProviderError:
            raise unavailable_error() from None
        names = {"email": "password", "google": "google"}
        return sorted({names[provider] for provider in providers if provider in names})

    async def get_active_account(self, account_id: UUID) -> Account | None:
        """Retourne le compte s'il existe et s'il est actif."""
        account = await self._accounts.get_by_id(account_id)
        return account if account is not None and account.is_active else None

    async def _create_account(
        self, *, username: str, password: str, auth_email: str, role: Role
    ) -> Account:
        """Crée l'identité puis le compte ; supprime l'identité si le compte échoue."""
        try:
            user_id = await self._identity.create_user(auth_email, password)
        except IdentityAlreadyExistsError:
            raise _username_taken() from None
        except IdentityProviderError:
            raise unavailable_error() from None
        try:
            return await self._accounts.create(
                account_id=user_id,
                username=username,
                display_name=username,
                auth_email=auth_email,
                role=role,
            )
        except UsernameAlreadyExistsError:
            await self._delete_orphan_identity(user_id)
            raise _username_taken() from None
        except Exception:
            await self._delete_orphan_identity(user_id)
            raise

    async def _equalize_timing(self, password: str) -> None:
        """Interroge le fournisseur pour un compte inexistant.

        Sans cet appel, un nom d'utilisateur inconnu répondrait nettement plus
        vite qu'un nom connu, ce qui permettrait d'énumérer les comptes.
        """
        try:
            await self._identity.sign_in(f"_unknown_@{self._email_domain}", password)
        except (InvalidCredentialsError, IdentityProviderError):
            return

    async def _delete_orphan_identity(self, user_id: UUID) -> None:
        try:
            await self._identity.delete_user(user_id)
        except IdentityProviderError:
            logger.error("Identité orpheline non supprimée", extra={"account_id": str(user_id)})

    async def _discard_session(self, tokens: SessionTokens) -> None:
        try:
            await self._identity.sign_out(tokens.access_token)
        except IdentityProviderError:
            logger.warning("Session du mauvais accès non révoquée")
