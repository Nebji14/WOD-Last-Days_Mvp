"""Liens de lecture des images : URL signées à durée limitée (bucket privé, US-031)."""

from typing import Protocol

from app.core.errors import AppError, ErrorCode
from app.domain.images import Image
from app.gateways.supabase_storage import StorageError

LINK_LIFETIME_SECONDS = 2 * 60 * 60
"""Durée de validité d'un lien ; le client relit la scène bien avant son expiration."""


class UrlSigner(Protocol):
    """Signature des chemins du bucket attendue par les services d'images."""

    async def signed_urls(self, paths: list[str], expires_in: int) -> dict[str, str]: ...


def storage_unavailable() -> AppError:
    """Erreur générique quand le stockage de fichiers ne répond pas."""
    return AppError(
        ErrorCode.SERVICE_UNAVAILABLE,
        "Les images sont momentanément indisponibles.",
        status_code=503,
    )


async def image_links(signer: UrlSigner, images: list[Image]) -> dict[str, str]:
    """Retourne l'URL signée de chaque image, par identifiant d'image.

    Raises:
        AppError: ``service_unavailable`` si le stockage ne répond pas.
    """
    try:
        by_path = await signer.signed_urls(
            [image.storage_path for image in images], LINK_LIFETIME_SECONDS
        )
    except StorageError:
        raise storage_unavailable() from None
    return {
        str(image.id): by_path[image.storage_path]
        for image in images
        if image.storage_path in by_path
    }
