"""Contrôle d'un fichier image envoyé, commun à la bibliothèque et aux portraits."""

from uuid import uuid4

from app.core.errors import AppError, ErrorCode
from app.domain.images import ImageType, detect_image_type


def image_too_large() -> AppError:
    """Fichier vide ou au-delà du poids accepté."""
    return AppError(ErrorCode.IMAGE_TOO_LARGE, "Image trop lourde.", status_code=413)


def checked_image_type(content: bytes, max_bytes: int) -> ImageType:
    """Retourne le type réel de l'image, lu sur la signature du fichier.

    Raises:
        AppError: ``image_too_large`` ou ``unsupported_image``.
    """
    if not content or len(content) > max_bytes:
        raise image_too_large()
    image_type = detect_image_type(content[:12])
    if image_type is None:
        raise AppError(ErrorCode.UNSUPPORTED_IMAGE, "Format d'image non accepté.", status_code=415)
    return image_type


def new_storage_path(image_type: ImageType) -> str:
    """Nom de fichier régénéré : jamais celui envoyé par le navigateur."""
    return f"{uuid4().hex}.{image_type.extension}"
