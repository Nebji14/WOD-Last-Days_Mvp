"""Catalogue de musique : recherche, lien collé et description d'un morceau.

Les réponses restent en mémoire : une recherche refaite dans la journée ou un
morceau déjà trouvé ne consomment pas le quota de la source.
"""

import time
from collections.abc import Callable
from typing import Protocol

from app.core.errors import AppError, ErrorCode
from app.domain.music import Track, video_id_from_link
from app.gateways.youtube import MusicNotConfiguredError, MusicQuotaError, MusicSourceError
from app.services.ttl_cache import TtlCache

_TTL_SECONDS = 24 * 3600.0
_MAX_SEARCHES = 200
_MAX_TRACKS = 2000


class MusicSource(Protocol):
    """Source de musique attendue par le catalogue."""

    async def search(self, query: str) -> list[Track]: ...
    async def describe(self, video_ids: list[str]) -> list[Track]: ...


def _source_error(error: MusicSourceError) -> AppError:
    if isinstance(error, MusicNotConfiguredError):
        return AppError(ErrorCode.MUSIC_NOT_CONFIGURED, "Musique non configurée.", status_code=503)
    if isinstance(error, MusicQuotaError):
        return AppError(ErrorCode.MUSIC_QUOTA_REACHED, "Quota épuisé.", status_code=503)
    return AppError(ErrorCode.SERVICE_UNAVAILABLE, "Service indisponible.", status_code=503)


class MusicCatalog:
    """Recherche des morceaux et retrouve la description d'un identifiant.

    Args:
        source: source de musique.
        clock: horloge monotone, remplaçable dans les tests.
    """

    def __init__(self, source: MusicSource, clock: Callable[[], float] = time.monotonic) -> None:
        self._source = source
        self._searches: TtlCache[list[Track]] = TtlCache(_MAX_SEARCHES, _TTL_SECONDS, clock)
        self._tracks: TtlCache[Track] = TtlCache(_MAX_TRACKS, _TTL_SECONDS, clock)

    async def search(self, query: str) -> list[Track]:
        """Cherche par texte, ou retrouve la vidéo d'un lien collé.

        Raises:
            AppError: ``music_not_configured``, ``music_quota_reached`` ou
                ``service_unavailable``.
        """
        linked = video_id_from_link(query)
        if linked is not None:
            track = await self._describe(linked)
            return [track] if track is not None else []
        key = " ".join(query.lower().split())
        if not key:
            return []
        known = self._searches.get(key)
        if known is not None:
            return known
        try:
            tracks = await self._source.search(key)
        except MusicSourceError as error:
            raise _source_error(error) from None
        self._searches.put(key, tracks)
        for track in tracks:
            self._tracks.put(track.video_id, track)
        return tracks

    async def track(self, video_id: str) -> Track:
        """Retourne la description d'un morceau.

        Raises:
            AppError: ``track_unavailable`` s'il n'existe pas ou ne se joue pas
                dans le lecteur, ou une panne de la source.
        """
        track = await self._describe(video_id)
        if track is None:
            raise AppError(ErrorCode.TRACK_UNAVAILABLE, "Morceau indisponible.", status_code=404)
        return track

    async def _describe(self, video_id: str) -> Track | None:
        known = self._tracks.get(video_id)
        if known is not None:
            return known
        try:
            found = await self._source.describe([video_id])
        except MusicSourceError as error:
            raise _source_error(error) from None
        for track in found:
            self._tracks.put(track.video_id, track)
        return found[0] if found else None
