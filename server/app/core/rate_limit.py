"""Limitation de débit en mémoire, par fenêtre glissante.

Suffisant pour une instance unique (10 utilisateurs simultanés au plus).
Un déploiement sur plusieurs instances demanderait un stockage partagé.
"""

import time
from collections import deque
from collections.abc import Callable

_CLEANUP_THRESHOLD = 5000


class RateLimiter:
    """Compte les événements par clé sur une fenêtre de temps glissante.

    Args:
        clock: source de temps monotone, remplaçable dans les tests.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    def allow(self, key: str, limit: int, window_seconds: float) -> bool:
        """Enregistre un événement et indique s'il respecte la limite.

        Args:
            key: identifiant de ce qui est limité (adresse, nom d'utilisateur…).
            limit: nombre maximal d'événements dans la fenêtre.
            window_seconds: durée de la fenêtre.

        Returns:
            ``True`` si l'événement est accepté, ``False`` si la limite est atteinte.
            Un événement refusé n'est pas compté.
        """
        now = self._clock()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        if len(self._hits) > _CLEANUP_THRESHOLD:
            self._drop_idle_keys(now, window_seconds)
        return True

    def _drop_idle_keys(self, now: float, window_seconds: float) -> None:
        """Libère les clés sans événement récent pour borner la mémoire."""
        idle = [
            key for key, hits in self._hits.items() if not hits or now - hits[-1] >= window_seconds
        ]
        for key in idle:
            del self._hits[key]
