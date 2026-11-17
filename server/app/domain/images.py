"""Règles pures de la bibliothèque d'images du MJ (US-031, écran 04b).

Aucun accès réseau ni base : type réel d'un fichier, noms, dossiers et pile
de la table.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

MAX_IMAGE_BYTES = 8 * 1024 * 1024
"""Poids maximal d'une image (04b-I1, limite fixée par le développeur)."""

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
    """Nom proposé pour une image chargée : le nom du fichier, sans extension (04b-I1).

    Les espaces superflus sont retirés et le nom est borné à ``IMAGE_NAME_MAX``.
    Un nom vide devient ``DEFAULT_IMAGE_NAME``.
    """
    stem = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    cleaned = " ".join(stem.split())[:IMAGE_NAME_MAX].strip()
    return cleaned or DEFAULT_IMAGE_NAME


def clean_name(name: str, limit: int) -> str | None:
    """Nom saisi, sans espaces superflus ; ``None`` s'il est vide ou trop long."""
    cleaned = " ".join(name.split())
    if not cleaned or len(cleaned) > limit:
        return None
    return cleaned


def would_create_cycle(
    parents: Mapping[UUID, UUID | None], folder_id: UUID, new_parent_id: UUID | None
) -> bool:
    """Indique si ranger ``folder_id`` sous ``new_parent_id`` créerait un cycle (04b-I10).

    Args:
        parents: parent de chaque dossier existant.
        folder_id: dossier déplacé.
        new_parent_id: futur parent, ``None`` pour la racine.

    Returns:
        ``True`` si le futur parent est le dossier lui-même ou l'un de ses descendants.
    """
    current = new_parent_id
    visited: set[UUID] = set()
    while current is not None and current not in visited:
        if current == folder_id:
            return True
        visited.add(current)
        current = parents.get(current)
    return False


@dataclass(frozen=True, slots=True)
class ImageFolder:
    """Dossier de la bibliothèque (décision du 2026-11-16)."""

    id: UUID
    name: str
    parent_id: UUID | None


@dataclass(frozen=True, slots=True)
class Image:
    """Image de la bibliothèque.

    Attributs:
        storage_path: nom de l'objet dans le bucket privé.
        is_shown: affichée en grand à la table (03-A2).
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
    """Images posées sur la table, la plus récente en premier (04b, Sur la table)."""
    posed = [image for image in images if image.on_table_at is not None]
    return sorted(posed, key=lambda image: image.on_table_at or image.created_at, reverse=True)
