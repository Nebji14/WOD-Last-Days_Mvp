"""Diffusion de la musique à toute la table.

Le droit d'accès (MJ uniquement) est contrôlé par les routes. L'état vit en
mémoire, comme la présence : un redémarrage du serveur arrête la musique, les
playlists sont conservées en base.
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.music import (
    MusicDeck,
    QueueFullError,
    QueueItem,
    RepeatMode,
    Track,
    UnknownItemError,
)

logger = logging.getLogger(__name__)

_MIN_WAIT_SECONDS = 0.05


@dataclass(frozen=True, slots=True)
class NowPlaying:
    """Ce que tous les participants entendent.

    Attributs:
        play_id: numéro de la lecture ; change à chaque lancement.
        position: position en secondes au moment où l'état est produit.
        video_shown: vidéo affichée en grand chez tous.
    """

    play_id: int
    track: Track | None
    playing: bool
    position: float
    video_shown: bool


@dataclass(frozen=True, slots=True)
class DeckState:
    """État complet pour le MJ : lecture, file d'attente et boucle."""

    now: NowPlaying
    queue: list[QueueItem]
    repeat: RepeatMode


class MusicBroadcaster(Protocol):
    """Diffusion en temps réel de la lecture."""

    async def music_changed(self, now: NowPlaying) -> None: ...


class MusicService:
    """Commandes de lecture du MJ et enchaînement automatique des morceaux.

    Args:
        broadcaster: diffusion vers tous les participants.
        clock: horloge monotone, remplaçable dans les tests.
        shuffle: mélange d'une playlist, remplaçable dans les tests.
    """

    def __init__(
        self,
        broadcaster: MusicBroadcaster,
        clock: Callable[[], float] = time.monotonic,
        shuffle: Callable[[list[Track]], None] = random.shuffle,
    ) -> None:
        self._broadcaster = broadcaster
        self._clock = clock
        self._shuffle = shuffle
        self._deck = MusicDeck()
        self._timer: asyncio.Task[None] | None = None

    def now_playing(self) -> NowPlaying:
        """Lecture en cours, vue par tous."""
        deck = self._deck
        return NowPlaying(
            play_id=deck.play_id,
            track=deck.current.track if deck.current else None,
            playing=deck.is_playing,
            position=deck.position(self._clock()),
            video_shown=deck.video_shown,
        )

    def deck(self) -> DeckState:
        """État complet, réservé au MJ."""
        return DeckState(self.now_playing(), list(self._deck.queue), self._deck.repeat)

    async def play(self, track: Track, show_video: bool = False) -> None:
        """Joue un morceau tout de suite, sans toucher à la file."""
        self._deck.play(track, self._clock(), show_video)
        await self._changed()

    async def show_video(self, shown: bool) -> None:
        """Affiche ou range, chez tous, la vidéo du morceau en cours."""
        self._deck.show_video(shown)
        await self._changed()

    async def play_all(self, tracks: Sequence[Track], shuffled: bool) -> None:
        """Lance une playlist, qui remplace la file."""
        ordered = list(tracks)
        if shuffled:
            self._shuffle(ordered)
        self._deck.play_all(ordered, self._clock())
        await self._changed()

    async def play_item(self, item_id: UUID) -> None:
        """Joue tout de suite un morceau de la file."""
        self._on_item(lambda: self._deck.play_item(item_id, self._clock()))
        await self._changed()

    async def enqueue(self, track: Track) -> None:
        """Ajoute un morceau en fin de file.

        Raises:
            AppError: ``music_list_full`` si la file est pleine.
        """
        try:
            self._deck.enqueue(track, self._clock())
        except QueueFullError:
            raise AppError(
                ErrorCode.MUSIC_LIST_FULL, "File d'attente pleine.", status_code=422
            ) from None
        await self._changed()

    async def remove(self, item_id: UUID) -> None:
        """Retire un morceau de la file."""
        self._on_item(lambda: self._deck.remove(item_id))
        await self._changed()

    async def move(self, item_id: UUID, index: int) -> None:
        """Déplace un morceau dans la file."""
        self._on_item(lambda: self._deck.move(item_id, index))
        await self._changed()

    async def clear_queue(self) -> None:
        """Vide la file sans arrêter le morceau en cours."""
        self._deck.clear_queue()
        await self._changed()

    async def pause(self) -> None:
        self._deck.pause(self._clock())
        await self._changed()

    async def resume(self) -> None:
        self._deck.resume(self._clock())
        await self._changed()

    async def seek(self, seconds: float) -> None:
        """Place la lecture à une position, chez tous."""
        self._deck.seek(seconds, self._clock())
        await self._changed()

    async def skip(self, play_id: int) -> None:
        """Passe au suivant. Sans effet si la lecture visée est déjà finie.

        Deux demandes simultanées (bouton et fin du morceau) ne sautent ainsi
        qu'un seul morceau.
        """
        if play_id == self._deck.play_id and self._deck.current is not None:
            self._deck.skip(self._clock())
            await self._changed()

    async def set_repeat(self, mode: RepeatMode) -> None:
        """Choisit la boucle."""
        self._deck.repeat = mode
        await self._changed()

    async def stop(self) -> None:
        """Arrête la musique ; la file est conservée."""
        self._deck.stop()
        await self._changed()

    async def finish_if_over(self) -> bool:
        """Enchaîne si le morceau est terminé. Retourne ``True`` s'il l'était."""
        now = self._clock()
        remaining = self._deck.remaining(now)
        if remaining is None or remaining > 0:
            return False
        self._deck.finish(now)
        await self._changed()
        return True

    def close(self) -> None:
        """Annule l'enchaînement programmé, à l'arrêt du serveur."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    @staticmethod
    def _on_item(action: Callable[[], None]) -> None:
        """Exécute une action sur un morceau de la file, qui peut en être déjà sorti."""
        try:
            action()
        except UnknownItemError:
            raise AppError(
                ErrorCode.NOT_FOUND, "Morceau introuvable dans la file.", status_code=404
            ) from None

    async def _changed(self) -> None:
        """Reprogramme la fin du morceau, puis diffuse le nouvel état."""
        self._schedule_end()
        await self._broadcaster.music_changed(self.now_playing())

    def _schedule_end(self) -> None:
        # La minuterie peut elle-même être à l'origine du changement : elle ne s'annule pas.
        if self._timer is not None and self._timer is not asyncio.current_task():
            self._timer.cancel()
        self._timer = None
        remaining = self._deck.remaining(self._clock())
        if remaining is not None:
            self._timer = asyncio.create_task(self._wait_for_end(remaining))

    async def _wait_for_end(self, remaining: float) -> None:
        """Attend la fin du morceau puis enchaîne."""
        await asyncio.sleep(remaining)
        try:
            # Le réveil peut précéder la fin de quelques millisecondes.
            while not await self.finish_if_over():
                left = self._deck.remaining(self._clock())
                if left is None:
                    return
                await asyncio.sleep(max(left, _MIN_WAIT_SECONDS))
        except Exception:
            logger.exception("Enchaînement de la musique impossible")
