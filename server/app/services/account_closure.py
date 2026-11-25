"""Cas d'usage du départ d'un joueur : désactiver, supprimer, réactiver un compte.

Désactiver garde toutes les données ; seul le MJ peut rendre l'accès. Supprimer
efface définitivement le compte, les personnages et les photos ; les messages
restent dans le chat, sans nom.
"""

import logging
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.accounts import Account, Role
from app.domain.chat import ChatMessage
from app.gateways.supabase_auth import IdentityProviderError
from app.realtime.codes import CLOSE_UNAUTHENTICATED
from app.repositories.account_closure import DeletedAccount
from app.services.account import OwnerConfirmation

logger = logging.getLogger(__name__)


class ClosureStore(Protocol):
    """Contrat d'écriture des départs."""

    async def disable(self, account_id: UUID, body: str) -> UUID | None: ...

    async def reactivate(self, account_id: UUID) -> bool: ...

    async def delete(self, account_id: UUID, body: str) -> DeletedAccount | None: ...


class NoticeReader(Protocol):
    """Lecture de l'annonce publiée dans le chat."""

    async def get(self, message_id: UUID) -> ChatMessage | None: ...


class ClosureIdentity(Protocol):
    """Contrat du fournisseur d'identité pour un départ."""

    async def sign_out_everywhere(self, access_token: str) -> None: ...

    async def delete_user(self, user_id: UUID) -> None: ...


class SeatLeaver(Protocol):
    """Table de jeu, d'où le joueur disparaît."""

    async def vacate(self, account_id: UUID) -> None: ...

    async def refresh(self) -> None: ...


class ClosureBroadcaster(Protocol):
    """Diffusion du départ et fermeture des connexions du joueur."""

    async def message_changed(self, message: ChatMessage) -> None: ...

    async def account_removed(self, account_id: UUID) -> None: ...

    async def close_account(self, account_id: UUID, code: int) -> None: ...


class PortraitRemover(Protocol):
    """Suppression d'une photo du stockage."""

    async def discard_path(self, path: str | None) -> None: ...


def _gone() -> AppError:
    return AppError(ErrorCode.NOT_AUTHENTICATED, "Authentification requise.", status_code=401)


class AccountClosureService:
    """Orchestre le départ d'un joueur et son retour.

    Args:
        store: écriture des départs.
        messages: lecture de l'annonce publiée.
        identity: fournisseur d'identité.
        owner_check: confirmation du titulaire.
        table: table de jeu.
        broadcaster: diffusion en temps réel.
        portraits: suppression des photos.
    """

    def __init__(
        self,
        store: ClosureStore,
        messages: NoticeReader,
        identity: ClosureIdentity,
        owner_check: OwnerConfirmation,
        table: SeatLeaver,
        broadcaster: ClosureBroadcaster,
        portraits: PortraitRemover,
    ) -> None:
        self._store = store
        self._messages = messages
        self._identity = identity
        self._owner_check = owner_check
        self._table = table
        self._broadcaster = broadcaster
        self._portraits = portraits

    async def disable(
        self,
        account: Account,
        *,
        username: str,
        password: str | None,
        authenticated_at: float | None,
        access_token: str,
    ) -> None:
        """Désactive le compte du joueur, à sa demande.

        Args:
            username: nom d'utilisateur recopié par le joueur.

        Raises:
            AppError: ``forbidden`` pour le MJ, ``confirmation_mismatch``,
                ``wrong_password``, ``reauthentication_required`` ou
                ``service_unavailable``.
        """
        await self._confirm(account, username, password, authenticated_at)
        message_id = await self._store.disable(
            account.id, f"{account.display_name} a quitté la campagne."
        )
        if message_id is None:
            raise _gone()
        try:
            await self._identity.sign_out_everywhere(access_token)
        except IdentityProviderError:
            # Le compte est déjà refusé partout : il reste des jetons sans effet.
            logger.warning("Sessions d'un compte désactivé non révoquées")
        await self._leave(account.id, message_id)

    async def delete(
        self,
        account: Account,
        *,
        username: str,
        password: str | None,
        authenticated_at: float | None,
    ) -> None:
        """Supprime définitivement le compte du joueur, à sa demande.

        Raises:
            AppError: comme ``disable``.
        """
        await self._confirm(account, username, password, authenticated_at)
        deleted = await self._store.delete(
            account.id, f"{account.display_name} a quitté définitivement la campagne."
        )
        if deleted is None:
            raise _gone()
        await self._broadcaster.account_removed(account.id)
        await self._leave(account.id, deleted.message_id)
        for path in deleted.portraits:
            await self._portraits.discard_path(path)
        try:
            await self._identity.delete_user(account.id)
        except IdentityProviderError:
            # Sans compte, cette identité n'ouvre plus rien ici.
            logger.error(
                "Identité d'un compte supprimé non effacée", extra={"account_id": str(account.id)}
            )

    async def reactivate(self, account_id: UUID) -> None:
        """Rend son accès à un joueur désactivé ; le droit (MJ) est contrôlé par la route.

        Raises:
            AppError: ``not_found`` si aucun joueur désactivé ne correspond.
        """
        if not await self._store.reactivate(account_id):
            raise AppError(ErrorCode.NOT_FOUND, "Joueur introuvable.", status_code=404)
        await self._table.refresh()

    async def _confirm(
        self, account: Account, username: str, password: str | None, authenticated_at: float | None
    ) -> None:
        """Le MJ ne part pas ; un joueur recopie son nom et prouve son identité."""
        if account.role is not Role.PLAYER:
            raise AppError(
                ErrorCode.FORBIDDEN, "Le compte du maître du jeu ne se ferme pas.", status_code=403
            )
        if username != account.username:
            raise AppError(
                ErrorCode.CONFIRMATION_MISMATCH,
                "Le nom d'utilisateur recopié ne correspond pas.",
                status_code=422,
            )
        await self._owner_check.confirm(account, password, authenticated_at)

    async def _leave(self, account_id: UUID, message_id: UUID) -> None:
        """Annonce le départ, libère la place et ferme toutes les fenêtres du joueur."""
        message = await self._messages.get(message_id)
        if message is not None:
            await self._broadcaster.message_changed(message)
        await self._table.vacate(account_id)
        await self._broadcaster.close_account(account_id, CLOSE_UNAUTHENTICATED)
