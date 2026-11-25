"""Mémoire bornée des réponses d'un service externe."""

from collections import OrderedDict
from collections.abc import Callable


class TtlCache[T]:
    """Les entrées expirent ; au-delà de la limite, les plus anciennes sont évincées.

    Args:
        limit: nombre maximal d'entrées.
        ttl_seconds: durée de vie d'une entrée.
        clock: horloge monotone, remplaçable dans les tests.
    """

    def __init__(self, limit: int, ttl_seconds: float, clock: Callable[[], float]) -> None:
        self._limit = limit
        self._ttl = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, T]] = OrderedDict()

    def get(self, key: str) -> T | None:
        """Retourne la valeur, ou ``None`` si elle est absente ou expirée."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        if self._clock() - entry[0] >= self._ttl:
            del self._entries[key]
            return None
        return entry[1]

    def put(self, key: str, value: T) -> None:
        """Retient une valeur."""
        self._entries[key] = (self._clock(), value)
        self._entries.move_to_end(key)
        while len(self._entries) > self._limit:
            self._entries.popitem(last=False)
