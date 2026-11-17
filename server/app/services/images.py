"""Bibliothèque d'images du MJ : images et dossiers (US-031, écran 04b).

Le droit d'accès (MJ uniquement) est contrôlé par les routes. Chaque
changement est signalé en temps réel : la pop-up Images et la table se
relisent (≤ 1 s, CDC 12.3).
"""

import logging
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from app.core.errors import AppError, ErrorCode
from app.domain.images import (
    FOLDER_NAME_MAX,
    IMAGE_NAME_MAX,
    MAX_IMAGE_BYTES,
    Image,
    ImageFolder,
    clean_name,
    detect_image_type,
    image_name_from_filename,
    would_create_cycle,
)
from app.gateways.supabase_storage import StorageError
from app.services.image_links import UrlSigner, image_links, storage_unavailable

logger = logging.getLogger(__name__)


class ImageStore(Protocol):
    """Accès aux images et aux dossiers attendu par le service."""

    async def list_folders(self) -> list[ImageFolder]: ...
    async def create_folder(self, name: str, parent_id: UUID | None) -> UUID: ...
    async def rename_folder(self, folder_id: UUID, name: str) -> bool: ...
    async def move_folder(self, folder_id: UUID, parent_id: UUID | None) -> None: ...
    async def delete_folder(self, folder_id: UUID, parent_id: UUID | None) -> None: ...
    async def list_images(self) -> list[Image]: ...
    async def get_image(self, image_id: UUID) -> Image | None: ...
    async def create_image(
        self,
        name: str,
        folder_id: UUID | None,
        storage_path: str,
        content_type: str,
        size_bytes: int,
    ) -> UUID: ...
    async def rename_image(self, image_id: UUID, name: str) -> None: ...
    async def move_image(self, image_id: UUID, folder_id: UUID | None) -> None: ...
    async def delete_image(self, image_id: UUID) -> None: ...


class FileStorage(UrlSigner, Protocol):
    """Stockage des fichiers attendu par le service."""

    async def upload(self, path: str, content: bytes, content_type: str) -> None: ...
    async def delete(self, path: str) -> None: ...


class ImageBroadcaster(Protocol):
    """Signal temps réel d'un changement de la bibliothèque ou de la table."""

    async def images_changed(self) -> None: ...


@dataclass(frozen=True, slots=True)
class Library:
    """Bibliothèque complète : dossiers, images et lien de lecture de chaque image."""

    folders: list[ImageFolder]
    images: list[Image]
    links: dict[str, str]


def _not_found() -> AppError:
    return AppError(ErrorCode.NOT_FOUND, "Élément introuvable.", status_code=404)


def _invalid_name() -> AppError:
    return AppError(ErrorCode.VALIDATION_ERROR, "Nom vide ou trop long.", status_code=422)


class ImageService:
    """Cas d'usage de la bibliothèque (CRUD des images et des dossiers, T1).

    Args:
        store: accès aux données.
        storage: dépôt, suppression et signature des fichiers.
        broadcaster: signal temps réel.
    """

    def __init__(
        self, store: ImageStore, storage: FileStorage, broadcaster: ImageBroadcaster
    ) -> None:
        self._store = store
        self._storage = storage
        self._broadcaster = broadcaster

    async def library(self) -> Library:
        """Retourne toute la bibliothèque (US-031 · CA1)."""
        images = await self._store.list_images()
        folders = await self._store.list_folders()
        return Library(folders, images, await image_links(self._storage, images))

    async def upload(self, filename: str, folder_id: UUID | None, content: bytes) -> Image:
        """Ajoute une image à la bibliothèque, dans le dossier ouvert (04b-I1).

        Le type est vérifié sur la signature du fichier, le nom du fichier
        stocké est régénéré.

        Raises:
            AppError: ``image_too_large``, ``unsupported_image``, ``not_found``
                (dossier absent) ou ``service_unavailable``.
        """
        if not content or len(content) > MAX_IMAGE_BYTES:
            raise AppError(ErrorCode.IMAGE_TOO_LARGE, "Image trop lourde.", status_code=413)
        image_type = detect_image_type(content[:12])
        if image_type is None:
            raise AppError(
                ErrorCode.UNSUPPORTED_IMAGE, "Format d'image non accepté.", status_code=415
            )
        await self._require_folder(folder_id)
        path = f"{uuid4().hex}.{image_type.extension}"
        try:
            await self._storage.upload(path, content, image_type.value)
        except StorageError:
            raise storage_unavailable() from None
        name = image_name_from_filename(filename)
        image_id = await self._store.create_image(
            name, folder_id, path, image_type.value, len(content)
        )
        await self._broadcaster.images_changed()
        return await self._image(image_id)

    async def rename_image(self, image_id: UUID, name: str) -> None:
        """Renomme une image (04b-I5)."""
        await self._image(image_id)
        await self._store.rename_image(image_id, self._name(name, IMAGE_NAME_MAX))
        await self._broadcaster.images_changed()

    async def move_image(self, image_id: UUID, folder_id: UUID | None) -> None:
        """Range une image dans un dossier, ou à la racine (04b-I10)."""
        await self._image(image_id)
        await self._require_folder(folder_id)
        await self._store.move_image(image_id, folder_id)
        await self._broadcaster.images_changed()

    async def delete_image(self, image_id: UUID) -> None:
        """Supprime une image, même posée sur la table : elle quitte aussi la pile (Q04b-2)."""
        image = await self._image(image_id)
        await self._store.delete_image(image_id)
        await self._broadcaster.images_changed()
        try:
            await self._storage.delete(image.storage_path)
        except StorageError:
            # La ligne est déjà supprimée : l'action du MJ reste réussie, le fichier
            # orphelin est signalé pour un nettoyage manuel.
            logger.warning("Fichier d'image non supprimé", extra={"image_id": str(image_id)})

    async def create_folder(self, name: str, parent_id: UUID | None) -> UUID:
        """Crée un dossier à la racine ou dans le dossier ouvert (04b-I9)."""
        await self._require_folder(parent_id)
        folder_id = await self._store.create_folder(self._name(name, FOLDER_NAME_MAX), parent_id)
        await self._broadcaster.images_changed()
        return folder_id

    async def rename_folder(self, folder_id: UUID, name: str) -> None:
        """Renomme un dossier (04b-I9)."""
        if not await self._store.rename_folder(folder_id, self._name(name, FOLDER_NAME_MAX)):
            raise _not_found()
        await self._broadcaster.images_changed()

    async def move_folder(self, folder_id: UUID, parent_id: UUID | None) -> None:
        """Range un dossier sous un autre ; refusé s'il créerait un cycle (04b-I10)."""
        parents = await self._parents()
        if folder_id not in parents or (parent_id is not None and parent_id not in parents):
            raise _not_found()
        if would_create_cycle(parents, folder_id, parent_id):
            raise AppError(
                ErrorCode.FOLDER_CYCLE,
                "Un dossier ne peut pas être rangé dans l'un de ses sous-dossiers.",
                status_code=422,
            )
        await self._store.move_folder(folder_id, parent_id)
        await self._broadcaster.images_changed()

    async def delete_folder(self, folder_id: UUID) -> None:
        """Supprime un dossier ; son contenu remonte au dossier parent (Q04b-4)."""
        parents = await self._parents()
        if folder_id not in parents:
            raise _not_found()
        await self._store.delete_folder(folder_id, parents[folder_id])
        await self._broadcaster.images_changed()

    async def _image(self, image_id: UUID) -> Image:
        image = await self._store.get_image(image_id)
        if image is None:
            raise _not_found()
        return image

    async def _parents(self) -> dict[UUID, UUID | None]:
        return {folder.id: folder.parent_id for folder in await self._store.list_folders()}

    async def _require_folder(self, folder_id: UUID | None) -> None:
        if folder_id is not None and folder_id not in await self._parents():
            raise _not_found()

    @staticmethod
    def _name(name: str, limit: int) -> str:
        cleaned = clean_name(name, limit)
        if cleaned is None:
            raise _invalid_name()
        return cleaned
