"""Client du stockage de fichiers de Supabase (bucket privé des images, US-031).

La clé d'administration ne quitte jamais le serveur. Le navigateur ne reçoit
que des URL signées, valables pour une durée limitée.
"""

import logging

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

IMAGE_BUCKET = "images"
_TIMEOUT_SECONDS = 30.0


class StorageError(Exception):
    """Le stockage de fichiers est injoignable ou a refusé l'opération."""


class SupabaseStorageGateway:
    """Dépose, supprime et signe les fichiers du bucket des images.

    Args:
        settings: configuration du serveur (adresse du projet et clé d'administration).
        client: client HTTP partagé, fermé par l'application à l'arrêt.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._base_url = f"{settings.supabase_url}/storage/v1"
        self._client = client
        secret = settings.supabase_secret_key.get_secret_value()
        self._headers = {"apikey": secret, "Authorization": f"Bearer {secret}"}

    async def upload(self, path: str, content: bytes, content_type: str) -> None:
        """Dépose un fichier ; un fichier déjà présent à ce chemin n'est jamais écrasé.

        Raises:
            StorageError: si le dépôt échoue.
        """
        response = await self._request(
            "POST",
            f"/object/{IMAGE_BUCKET}/{path}",
            content=content,
            headers={**self._headers, "Content-Type": content_type, "x-upsert": "false"},
        )
        self._raise_for_status(response, "dépôt")

    async def delete(self, path: str) -> None:
        """Supprime un fichier. Un fichier déjà absent n'est pas une erreur.

        Raises:
            StorageError: si la suppression échoue.
        """
        response = await self._request(
            "DELETE",
            f"/object/{IMAGE_BUCKET}",
            json={"prefixes": [path]},
            headers=self._headers,
        )
        self._raise_for_status(response, "suppression")

    async def signed_urls(self, paths: list[str], expires_in: int) -> dict[str, str]:
        """Produit une URL signée par fichier, en un seul appel.

        Args:
            paths: chemins des fichiers dans le bucket.
            expires_in: durée de validité, en secondes.

        Returns:
            L'URL complète de chaque chemin ; un fichier introuvable est absent.

        Raises:
            StorageError: si la signature échoue.
        """
        if not paths:
            return {}
        response = await self._request(
            "POST",
            f"/object/sign/{IMAGE_BUCKET}",
            json={"expiresIn": expires_in, "paths": paths},
            headers=self._headers,
        )
        self._raise_for_status(response, "signature")
        urls: dict[str, str] = {}
        for item in response.json():
            signed = item.get("signedURL")
            if isinstance(signed, str) and isinstance(item.get("path"), str):
                urls[item["path"]] = f"{self._base_url}{signed}"
        return urls

    async def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        """Exécute une requête et convertit les pannes réseau en erreur du domaine."""
        try:
            return await self._client.request(
                method,
                f"{self._base_url}{path}",
                timeout=_TIMEOUT_SECONDS,
                **kwargs,  # type: ignore[arg-type]
            )
        except httpx.HTTPError as exc:
            logger.error("Stockage de fichiers injoignable", exc_info=exc)
            raise StorageError from exc

    @staticmethod
    def _raise_for_status(response: httpx.Response, operation: str) -> None:
        """Journalise et signale une réponse en erreur, sans détail côté client."""
        if response.is_success:
            return
        logger.error(
            "Opération de stockage refusée",
            extra={"operation": operation, "status": response.status_code},
        )
        raise StorageError
