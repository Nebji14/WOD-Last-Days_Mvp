"""Cas d'usage de la photo du maître du jeu, rattachée à son compte."""

from typing import Protocol
from uuid import UUID

from app.domain.accounts import Account
from app.domain.portraits import MAX_PORTRAIT_BYTES
from app.repositories.portraits import PortraitChange
from app.services.account import AccountBroadcaster, AccountRefresher
from app.services.character_access import not_found
from app.services.portraits import PortraitFiles


class AccountPortraitStore(Protocol):
    """Contrat d'écriture de la photo d'un compte."""

    async def set_account_portrait(
        self, account_id: UUID, path: str | None
    ) -> PortraitChange | None: ...


class AccountReader(Protocol):
    """Lecture d'un compte."""

    async def get_by_id(self, account_id: UUID) -> Account | None: ...


class AccountPortraitService:
    """Orchestre la photo du MJ ; le droit (MJ seul) est contrôlé par les routes.

    Args:
        store: écriture de la photo.
        accounts: relecture du compte.
        files: dépôt et suppression des fichiers.
        table: état de la table, où la photo est affichée.
        broadcaster: diffusion en temps réel.
    """

    def __init__(
        self,
        store: AccountPortraitStore,
        accounts: AccountReader,
        files: PortraitFiles,
        table: AccountRefresher,
        broadcaster: AccountBroadcaster,
    ) -> None:
        self._store = store
        self._accounts = accounts
        self._files = files
        self._table = table
        self._broadcaster = broadcaster

    async def replace(self, account: Account, content: bytes) -> Account:
        """Donne une photo au compte, à la place de la précédente.

        Raises:
            AppError: ``image_too_large``, ``unsupported_image`` ou
                ``service_unavailable``.
        """

        async def link(path: str) -> PortraitChange | None:
            return await self._store.set_account_portrait(account.id, path)

        await self._files.store(content, MAX_PORTRAIT_BYTES, link)
        return await self._changed(account.id)

    async def remove(self, account: Account) -> Account:
        """Retire la photo du compte. Sans effet s'il n'en a pas."""
        change = await self._store.set_account_portrait(account.id, None)
        if change is not None:
            await self._files.discard_path(change.previous)
        return await self._changed(account.id)

    async def _changed(self, account_id: UUID) -> Account:
        """Relit le compte et met à jour la table et les fenêtres ouvertes."""
        updated = await self._accounts.get_by_id(account_id)
        if updated is None:
            raise not_found()
        await self._broadcaster.account_changed(updated)
        await self._table.refresh_account(updated)
        return updated
