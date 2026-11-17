"""Doublures des images : dépôt et stockage de fichiers en mémoire."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domain.images import Image, ImageFolder
from app.gateways.supabase_storage import StorageError


class FakeImageStore:
    """Images et dossiers en mémoire, avec la même scène de table que la base."""

    def __init__(self) -> None:
        self.folders: dict[UUID, ImageFolder] = {}
        self.images: dict[UUID, Image] = {}
        self._clock = datetime(2026, 11, 17, tzinfo=UTC)

    def _now(self) -> datetime:
        self._clock += timedelta(seconds=1)
        return self._clock

    async def list_folders(self) -> list[ImageFolder]:
        return sorted(self.folders.values(), key=lambda f: f.name.lower())

    async def create_folder(self, name: str, parent_id: UUID | None) -> UUID:
        folder = ImageFolder(uuid4(), name, parent_id)
        self.folders[folder.id] = folder
        return folder.id

    async def rename_folder(self, folder_id: UUID, name: str) -> bool:
        if folder_id not in self.folders:
            return False
        self.folders[folder_id] = replace(self.folders[folder_id], name=name)
        return True

    async def move_folder(self, folder_id: UUID, parent_id: UUID | None) -> None:
        self.folders[folder_id] = replace(self.folders[folder_id], parent_id=parent_id)

    async def delete_folder(self, folder_id: UUID, parent_id: UUID | None) -> None:
        for image in list(self.images.values()):
            if image.folder_id == folder_id:
                self.images[image.id] = replace(image, folder_id=parent_id)
        for folder in list(self.folders.values()):
            if folder.parent_id == folder_id:
                self.folders[folder.id] = replace(folder, parent_id=parent_id)
        del self.folders[folder_id]

    async def list_images(self) -> list[Image]:
        return sorted(self.images.values(), key=lambda i: i.name.lower())

    async def get_image(self, image_id: UUID) -> Image | None:
        return self.images.get(image_id)

    async def create_image(
        self,
        name: str,
        folder_id: UUID | None,
        storage_path: str,
        content_type: str,
        size_bytes: int,
    ) -> UUID:
        image = Image(
            uuid4(),
            name,
            folder_id,
            storage_path,
            content_type,
            size_bytes,
            is_shown=False,
            on_table_at=None,
            created_at=self._now(),
        )
        self.images[image.id] = image
        return image.id

    async def rename_image(self, image_id: UUID, name: str) -> None:
        self.images[image_id] = replace(self.images[image_id], name=name)

    async def move_image(self, image_id: UUID, folder_id: UUID | None) -> None:
        self.images[image_id] = replace(self.images[image_id], folder_id=folder_id)

    async def delete_image(self, image_id: UUID) -> None:
        del self.images[image_id]

    async def show(self, image_id: UUID) -> None:
        for image in list(self.images.values()):
            if image.is_shown and image.id != image_id:
                self.images[image.id] = replace(image, is_shown=False, on_table_at=self._now())
        self.images[image_id] = replace(self.images[image_id], is_shown=True)

    async def put_down(self) -> UUID | None:
        shown = next((i for i in self.images.values() if i.is_shown), None)
        if shown is None:
            return None
        self.images[shown.id] = replace(shown, is_shown=False, on_table_at=self._now())
        return shown.id

    async def remove_from_table(self, image_id: UUID) -> None:
        self.images[image_id] = replace(self.images[image_id], on_table_at=None, is_shown=False)


class FakeFileStorage:
    """Stockage de fichiers en mémoire. ``available = False`` simule une panne."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.available = True

    def _check(self) -> None:
        if not self.available:
            raise StorageError

    async def upload(self, path: str, content: bytes, content_type: str) -> None:
        self._check()
        self.files[path] = content

    async def delete(self, path: str) -> None:
        self._check()
        self.files.pop(path, None)

    async def signed_urls(self, paths: list[str], expires_in: int) -> dict[str, str]:
        self._check()
        return {p: f"https://storage.test/{p}?ttl={expires_in}" for p in paths if p in self.files}
