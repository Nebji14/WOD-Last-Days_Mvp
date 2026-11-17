"""Règles pures de la bibliothèque d'images du MJ.

Aucun accès réseau ni base : type réel d'un fichier, noms, dossiers et pile
de la table.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

MAX_IMAGE_BYTES = 8 * 1024 * 1024
"""Poids maximal d'une image chargée."""

IMAGE_NAME_MAX = 120
FOLDER_NAME_MAX = 60
DEFAULT_IMAGE_NAME = "Image"


class ImageType(StrEnum):
    """Formats acceptés, reconnus à la signature du fichier et non à son extension."""

    PNG = "image/png"
    JPEG = "image/jpeg"
    WEBP = "image/webp"
    GIF = "image/gif"

    @property
    def extension(self) -> str:
        """Extension du fichier régénéré dans le stockage."""
        return _EXTENSIONS[self]


_EXTENSIONS = {
    ImageType.PNG: "png",
    ImageType.JPEG: "jpg",
    ImageType.WEBP: "webp",
    ImageType.GIF: "gif",
}


def detect_image_type(head: bytes) -> ImageType | None:
    """Reconnaît le type réel d'une image d'après ses premiers octets.

    Args:
        head: début du fichier (12 octets suffisent).

    Returns:
        Le type reconnu, ou ``None`` si le fichier n'est pas une image acceptée.
    """
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ImageType.PNG
    if head.startswith(b"\xff\xd8\xff"):
        return ImageType.JPEG
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ImageType.WEBP
    if head.startswith((b"GIF87a", b"GIF89a")):
        return ImageType.GIF
    return None


def image_name_from_filename(filename: str) -> str:
    """Nom proposé pour une image chargée : le nom du fichier, sans extension.

    Les espaces superflus sont retirés et le nom est borné à ``IMAGE_NAME_MAX``.
    Un nom vide devient ``DEFAULT_IMAGE_NAME``.
    """
    stem = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    cleaned = " ".join(stem.split())[:IMAGE_NAME_MAX].strip()
    return cleaned or DEFAULT_IMAGE_NAME


@dataclass(frozen=True, slots=True)
class ImageFolder:
    """Dossier de la bibliothèque d'images, rangé ou non dans un dossier parent."""

    id: UUID
    name: str
    parent_id: UUID | None


@dataclass(frozen=True, slots=True)
class Image:
    """Image de la bibliothèque.

    Attributs:
        storage_path: nom de l'objet dans le bucket privé.
        is_shown: affichée en grand à la table.
        on_table_at: date de pose sur la pile ; ``None`` hors de la table.
    """

    id: UUID
    name: str
    folder_id: UUID | None
    storage_path: str
    content_type: str
    size_bytes: int
    is_shown: bool
    on_table_at: datetime | None
    created_at: datetime


def table_pile(images: list[Image]) -> list[Image]:
    """Images posées sur la table, la plus récente en premier."""
    posed = [image for image in images if image.on_table_at is not None]
    return sorted(posed, key=lambda image: image.on_table_at or image.created_at, reverse=True)
