"""Modèles d'entrée et de sortie des images (US-031, écrans 04b et 08a)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.images import FOLDER_NAME_MAX, IMAGE_NAME_MAX, Image, ImageFolder
from app.services.image_table import TableScene
from app.services.images import Library


class FolderResponse(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None

    @classmethod
    def from_folder(cls, folder: ImageFolder) -> "FolderResponse":
        return cls(id=folder.id, name=folder.name, parent_id=folder.parent_id)


class ImageResponse(BaseModel):
    """Image et son lien de lecture signé, ``None`` si le fichier est introuvable."""

    id: UUID
    name: str
    folder_id: UUID | None
    url: str | None
    is_shown: bool
    on_table_at: datetime | None

    @classmethod
    def from_image(cls, image: Image, links: dict[str, str]) -> "ImageResponse":
        return cls(
            id=image.id,
            name=image.name,
            folder_id=image.folder_id,
            url=links.get(str(image.id)),
            is_shown=image.is_shown,
            on_table_at=image.on_table_at,
        )


class LibraryResponse(BaseModel):
    folders: list[FolderResponse]
    images: list[ImageResponse]

    @classmethod
    def from_library(cls, library: Library) -> "LibraryResponse":
        return cls(
            folders=[FolderResponse.from_folder(f) for f in library.folders],
            images=[ImageResponse.from_image(i, library.links) for i in library.images],
        )


class SceneResponse(BaseModel):
    """Images de la table, vues par tous les participants (03-A2, 03-I5)."""

    shown: ImageResponse | None
    pile: list[ImageResponse]

    @classmethod
    def from_scene(cls, scene: TableScene) -> "SceneResponse":
        return cls(
            shown=ImageResponse.from_image(scene.shown, scene.links) if scene.shown else None,
            pile=[ImageResponse.from_image(i, scene.links) for i in scene.pile],
        )


class RenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=IMAGE_NAME_MAX)


class MoveImageRequest(BaseModel):
    """Dossier de destination ; ``None`` pour « Toutes les images » (racine)."""

    folder_id: UUID | None


class FolderRequest(BaseModel):
    name: str = Field(min_length=1, max_length=FOLDER_NAME_MAX)
    parent_id: UUID | None = None


class FolderRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=FOLDER_NAME_MAX)


class MoveFolderRequest(BaseModel):
    parent_id: UUID | None


class CreatedResponse(BaseModel):
    id: UUID
