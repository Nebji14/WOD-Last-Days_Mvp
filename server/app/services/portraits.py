"""Cas d'usage des portraits : chaque forme d'un personnage porte sa propre image."""

import logging
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.accounts import Account
from app.domain.character import Character, Sheet
from app.domain.images import ImageType, detect_image_type
from app.domain.portraits import (
    MAX_ORIGINAL_BYTES,
    MAX_PORTRAIT_BYTES,
    PortraitOwner,
    can_reframe_portrait,
    can_see_portrait,
    original_path,
)
from app.gateways.supabase_storage import StorageError
from app.repositories.portraits import PortraitChange
from app.repositories.sheet_items import ItemKind
from app.services.character_access import CharacterAccess, not_found
from app.services.image_links import storage_unavailable
from app.services.uploads import checked_image_type, new_storage_path

logger = logging.getLogger(__name__)


class PortraitStore(Protocol):
    """Contrat d'accès aux portraits attendu par le service."""

    async def set_portrait(self, sheet_id: UUID, path: str | None) -> PortraitChange | None: ...

    async def owner_of(self, path: str) -> PortraitOwner | None: ...


class SheetLocator(Protocol):
    """Retrouve le personnage auquel appartient une forme."""

    async def character_id_of(self, kind: ItemKind, item_id: UUID) -> UUID | None: ...


class FileDepot(Protocol):
    """Dépôt et suppression d'un fichier du stockage."""

    async def upload(self, path: str, content: bytes, content_type: str) -> None: ...

    async def delete(self, path: str) -> None: ...


class PortraitStorage(FileDepot, Protocol):
    """Stockage des fichiers attendu par le service."""

    async def download(self, path: str) -> bytes | None: ...


@dataclass(frozen=True, slots=True)
class PortraitFile:
    """Contenu d'un portrait et son type réel."""

    content: bytes
    type: ImageType


class PortraitFiles:
    """Dépose les fichiers des portraits et supprime ceux qui ne servent plus.

    Args:
        storage: stockage des fichiers.
    """

    def __init__(self, storage: FileDepot) -> None:
        self._storage = storage

    async def store(
        self,
        content: bytes,
        max_bytes: int,
        link: Callable[[str], Awaitable[PortraitChange | None]],
    ) -> None:
        """Dépose une image, l'enregistre en base, puis supprime celle qu'elle remplace.

        Args:
            link: enregistre le nom du fichier ; ``None`` si son sujet n'existe plus.

        Raises:
            AppError: ``image_too_large``, ``unsupported_image``, ``not_found``
                ou ``service_unavailable``.
        """
        image_type = checked_image_type(content, max_bytes)
        path = new_storage_path(image_type)
        try:
            await self._storage.upload(path, content, image_type.value)
        except StorageError:
            raise storage_unavailable() from None
        try:
            change = await link(path)
        except Exception:
            # Le fichier vient d'être déposé : sans ligne en base, personne ne le lirait.
            await self.discard_path(path)
            raise
        if change is None:
            await self.discard_path(path)
            raise not_found()
        await self.discard_path(change.previous)

    async def discard(self, sheets: Iterable[Sheet]) -> None:
        """Supprime les portraits de formes qui viennent d'être supprimées."""
        for sheet in sheets:
            await self.discard_path(sheet.portrait)

    async def discard_path(self, path: str | None) -> None:
        """Supprime un portrait et sa photo entière.

        Un échec laisse un fichier orphelin, signalé dans les logs.
        """
        if path is None:
            return
        for stored in (path, original_path(path)):
            try:
                await self._storage.delete(stored)
            except StorageError:
                logger.warning("Fichier de portrait non supprimé", extra={"portrait": stored})


class PortraitService:
    """Orchestre les portraits.

    Args:
        store: accès aux données.
        locator: retrouve le personnage auquel appartient une forme.
        storage: stockage des fichiers.
        files: suppression des fichiers remplacés.
        access: droits, relecture et diffusion.
    """

    def __init__(
        self,
        store: PortraitStore,
        locator: SheetLocator,
        storage: PortraitStorage,
        files: PortraitFiles,
        access: CharacterAccess,
    ) -> None:
        self._store = store
        self._locator = locator
        self._storage = storage
        self._files = files
        self._access = access

    async def replace(self, actor: Account, sheet_id: UUID, content: bytes) -> Character:
        """Donne une image à une forme, à la place de la précédente.

        Raises:
            AppError: ``not_found``, ``image_too_large``, ``unsupported_image``
                ou ``service_unavailable``.
        """
        character = await self._editable(actor, sheet_id)

        async def link(path: str) -> PortraitChange | None:
            return await self._store.set_portrait(sheet_id, path)

        await self._files.store(content, MAX_PORTRAIT_BYTES, link)
        return await self._access.changed(character.id)

    async def remove(self, actor: Account, sheet_id: UUID) -> Character:
        """Retire l'image d'une forme. Sans effet si elle n'en a pas."""
        character = await self._editable(actor, sheet_id)
        change = await self._store.set_portrait(sheet_id, None)
        if change is not None:
            await self._files.discard_path(change.previous)
        return await self._access.changed(character.id)

    async def read(self, actor: Account, path: str) -> PortraitFile:
        """Retourne l'image demandée.

        Raises:
            AppError: ``not_found`` si elle n'existe pas ou n'est pas visible
                par l'acteur ; ``service_unavailable``.
        """
        owner = await self._store.owner_of(path)
        if owner is None or not can_see_portrait(actor, owner):
            raise not_found()
        return await self._download(path)

    async def store_original(self, actor: Account, name: str, content: bytes) -> None:
        """Garde la photo entière d'un portrait, pour le recadrer plus tard.

        Raises:
            AppError: ``not_found``, ``image_too_large``, ``unsupported_image``
                ou ``service_unavailable``.
        """
        await self._require_reframing(actor, name)
        image_type = checked_image_type(content, MAX_ORIGINAL_BYTES)
        path = original_path(name)
        try:
            # Un envoi rejoué après une coupure remplace le précédent.
            await self._storage.delete(path)
            await self._storage.upload(path, content, image_type.value)
        except StorageError:
            raise storage_unavailable() from None

    async def read_original(self, actor: Account, name: str) -> PortraitFile:
        """Retourne la photo entière d'un portrait.

        Raises:
            AppError: ``not_found`` si elle n'a pas été gardée ou n'est pas
                accessible à l'acteur ; ``service_unavailable``.
        """
        await self._require_reframing(actor, name)
        return await self._download(original_path(name))

    async def _require_reframing(self, actor: Account, name: str) -> None:
        owner = await self._store.owner_of(name)
        if owner is None or not can_reframe_portrait(actor, owner):
            raise not_found()

    async def _download(self, path: str) -> PortraitFile:
        """Lit un fichier et reconnaît son type réel."""
        try:
            content = await self._storage.download(path)
        except StorageError:
            raise storage_unavailable() from None
        image_type = None if content is None else detect_image_type(content[:12])
        if content is None or image_type is None:
            raise not_found()
        return PortraitFile(content, image_type)

    async def _editable(self, actor: Account, sheet_id: UUID) -> Character:
        """Retourne le personnage modifiable auquel appartient la forme."""
        character_id = await self._locator.character_id_of(ItemKind.SHEET, sheet_id)
        return await self._access.editable(actor, character_id)
