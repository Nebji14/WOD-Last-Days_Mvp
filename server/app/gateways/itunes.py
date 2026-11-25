"""Client de l'API publique de recherche d'iTunes, pour les suggestions de saisie.

Seuls les noms d'artistes et les titres sont lus : ni extrait audio, ni pochette.
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_URL = "https://itunes.apple.com/search"
_TIMEOUT_SECONDS = 4.0
_RESULT_COUNT = 10
_COUNTRY = "FR"


class SuggestionSourceError(Exception):
    """La source de suggestions est injoignable ou a refusé la demande."""


@dataclass(frozen=True, slots=True)
class SongName:
    """Nom d'un morceau connu."""

    artist: str
    title: str


class ItunesGateway:
    """Recherche de noms de morceaux.

    Args:
        client: client HTTP partagé, fermé par l'application à l'arrêt.
    """

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def songs(self, query: str) -> list[SongName]:
        """Retourne les morceaux proches d'un texte, même incomplet.

        Raises:
            SuggestionSourceError: si la lecture échoue.
        """
        try:
            response = await self._client.get(
                _URL,
                params={
                    "term": query,
                    "media": "music",
                    "entity": "song",
                    "limit": str(_RESULT_COUNT),
                    "country": _COUNTRY,
                },
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # Le type suffit : le détail contiendrait le texte saisi.
            logger.warning("Suggestions indisponibles", extra={"error": type(exc).__name__})
            raise SuggestionSourceError from None
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list):
            raise SuggestionSourceError
        return [song for item in results if (song := _song(item)) is not None]


def _song(item: object) -> SongName | None:
    if not isinstance(item, dict):
        return None
    artist, title = item.get("artistName"), item.get("trackName")
    if not isinstance(artist, str) or not isinstance(title, str):
        return None
    return SongName(artist, title)
