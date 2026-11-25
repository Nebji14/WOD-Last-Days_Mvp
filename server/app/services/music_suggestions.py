"""Suggestions pendant la saisie d'une recherche de musique.

Elles ne consomment aucune recherche du quota. Ce n'est qu'un confort : une
source en panne ou trop sollicitée donne une liste vide, jamais une erreur.
"""

import time
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Protocol

from app.core.rate_limit import RateLimiter
from app.gateways.itunes import SongName, SuggestionSourceError
from app.services.ttl_cache import TtlCache

_TTL_SECONDS = 24 * 3600.0
_MAX_ENTRIES = 1000
_MAX_SUGGESTIONS = 8
_MAX_LENGTH = 120
# La source accepte environ 20 appels par minute : on reste en dessous.
_CALL_LIMIT = 18
_CALL_WINDOW_SECONDS = 60.0


class SuggestionSource(Protocol):
    """Source de noms de morceaux attendue par le service."""

    async def songs(self, query: str) -> list[SongName]: ...


def suggestions_from(songs: Sequence[SongName]) -> list[str]:
    """Textes proposés : les artistes qui reviennent, puis « artiste - titre », sans doublon."""
    artists = Counter(song.artist for song in songs)
    repeated = [artist for artist, count in artists.most_common(2) if count > 1]
    candidates = repeated + [f"{song.artist} - {song.title}" for song in songs]
    unique: dict[str, str] = {}
    for candidate in candidates:
        if len(candidate) <= _MAX_LENGTH:
            unique.setdefault(candidate.casefold(), candidate)
    return list(unique.values())[:_MAX_SUGGESTIONS]


class MusicSuggestionService:
    """Propose des recherches à partir d'un texte en cours de saisie.

    Args:
        source: source de noms de morceaux.
        clock: horloge monotone, remplaçable dans les tests.
    """

    def __init__(
        self, source: SuggestionSource, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._source = source
        self._cache: TtlCache[list[str]] = TtlCache(_MAX_ENTRIES, _TTL_SECONDS, clock)
        self._limiter = RateLimiter(clock)

    async def suggest(self, query: str) -> list[str]:
        """Retourne les suggestions, la plus pertinente en premier."""
        key = " ".join(query.lower().split())
        known = self._cache.get(key)
        if known is not None:
            return known
        if not key or not self._limiter.allow("source", _CALL_LIMIT, _CALL_WINDOW_SECONDS):
            return []
        try:
            found = suggestions_from(await self._source.songs(key))
        except SuggestionSourceError:
            return []
        self._cache.put(key, found)
        return found
