"""Client de l'API officielle de YouTube : recherche et description de vidéos.

La clé est transmise dans un en-tête et non dans l'adresse, pour ne figurer dans
aucun journal. Seules les vidéos que le lecteur intégré peut jouer sont retenues.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.domain.music import Track, duration_seconds, is_video_id

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.googleapis.com/youtube/v3"
_TIMEOUT_SECONDS = 10.0
_RESULT_COUNT = 20
_REGION = "FR"
_LANGUAGE = "fr"
_QUOTA_REASONS = frozenset({"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"})


class MusicSourceError(Exception):
    """La source de musique est injoignable ou a refusé la demande."""


class MusicNotConfiguredError(MusicSourceError):
    """Aucune clé d'accès n'est configurée."""


class MusicQuotaError(MusicSourceError):
    """Le quota quotidien est épuisé."""


class YouTubeGateway:
    """Recherche et description de vidéos.

    Args:
        settings: configuration du serveur (clé d'accès).
        client: client HTTP partagé, fermé par l'application à l'arrêt.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._key = settings.youtube_api_key.get_secret_value()
        self._client = client

    async def search(self, query: str) -> list[Track]:
        """Cherche des morceaux par texte libre. Consomme une recherche du quota.

        Raises:
            MusicSourceError: si la recherche échoue.
        """
        data = await self._get(
            "/search",
            {
                "part": "id",
                "q": query,
                "type": "video",
                "videoEmbeddable": "true",
                "videoSyndicated": "true",
                "maxResults": str(_RESULT_COUNT),
                "regionCode": _REGION,
                "relevanceLanguage": _LANGUAGE,
            },
        )
        ids = [video_id for item in _items(data) if (video_id := _search_id(item)) is not None]
        return await self.describe(ids)

    async def describe(self, video_ids: list[str]) -> list[Track]:
        """Décrit des vidéos, dans l'ordre demandé ; celles qui ne se jouent pas sont omises.

        Raises:
            MusicSourceError: si la lecture échoue.
        """
        if not video_ids:
            return []
        data = await self._get(
            "/videos", {"part": "snippet,contentDetails,status", "id": ",".join(video_ids)}
        )
        tracks = [track for item in _items(data) if (track := _track(item)) is not None]
        by_id = {track.video_id: track for track in tracks}
        return [by_id[video_id] for video_id in video_ids if video_id in by_id]

    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        """Appelle l'API et convertit ses refus en erreurs du domaine."""
        if not self._key:
            raise MusicNotConfiguredError
        try:
            response = await self._client.get(
                f"{_BASE_URL}{path}",
                params=params,
                headers={"X-Goog-Api-Key": self._key},
                timeout=_TIMEOUT_SECONDS,
            )
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # Le type suffit : le détail pourrait contenir la recherche saisie.
            logger.error("Source de musique injoignable", extra={"error": type(exc).__name__})
            raise MusicSourceError from None
        if response.is_success and isinstance(data, dict):
            return data
        reason = _error_reason(data)
        logger.error(
            "Source de musique en erreur",
            extra={"status": response.status_code, "reason": reason},
        )
        if reason in _QUOTA_REASONS:
            raise MusicQuotaError
        raise MusicSourceError


def _items(data: dict[str, Any]) -> list[dict[str, Any]]:
    items = data.get("items")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _search_id(item: dict[str, Any]) -> str | None:
    identifier = item.get("id")
    video_id = identifier.get("videoId") if isinstance(identifier, dict) else None
    return video_id if isinstance(video_id, str) and is_video_id(video_id) else None


def _track(item: dict[str, Any]) -> Track | None:
    """Convertit une vidéo ; ``None`` si elle est en direct ou interdite d'intégration."""
    try:
        video_id = str(item["id"])
        title = str(item["snippet"]["title"])
        channel = str(item["snippet"]["channelTitle"])
        duration = duration_seconds(str(item["contentDetails"]["duration"]))
        embeddable = item["status"]["embeddable"] is True
    except (KeyError, TypeError):
        return None
    if not embeddable or duration <= 0 or not is_video_id(video_id):
        return None
    return Track(video_id, title[:200], channel[:120], duration)


def _error_reason(data: object) -> str | None:
    """Motif de refus indiqué par l'API, ``None`` s'il est absent."""
    error = data.get("error") if isinstance(data, dict) else None
    errors = error.get("errors") if isinstance(error, dict) else None
    first = errors[0] if isinstance(errors, list) and errors else None
    reason = first.get("reason") if isinstance(first, dict) else None
    return reason if isinstance(reason, str) else None
