"""Règles pures de la musique : morceaux, liens, playlists et lecture commune.

Aucun accès réseau ni base. L'heure est toujours fournie par l'appelant, en
secondes d'une horloge qui ne recule pas.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

PLAYLIST_NAME_MAX = 60
PLAYLIST_TRACKS_MAX = 200
QUEUE_MAX = 200
SEARCH_QUERY_MAX = 200
SUGGESTION_QUERY_MIN = 3
SUGGESTION_QUERY_MAX = 80

_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_DURATION = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?")
_WATCH_HOSTS = frozenset({"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"})
_SHORT_HOST = "youtu.be"
_PATH_PREFIXES = frozenset({"embed", "shorts", "live"})


@dataclass(frozen=True, slots=True)
class Track:
    """Morceau que le lecteur peut jouer."""

    video_id: str
    title: str
    channel: str
    duration_seconds: int


@dataclass(frozen=True, slots=True)
class QueueItem:
    """Morceau placé dans la file. Le même morceau peut y figurer plusieurs fois."""

    id: UUID
    track: Track


@dataclass(frozen=True, slots=True)
class PlaylistTrack:
    """Morceau rangé dans une playlist."""

    id: UUID
    track: Track


@dataclass(frozen=True, slots=True)
class Playlist:
    """Playlist préparée par le MJ, dans l'ordre de lecture."""

    id: UUID
    name: str
    created_at: datetime
    tracks: tuple[PlaylistTrack, ...]


class RepeatMode(StrEnum):
    """Ce qui se passe à la fin d'un morceau."""

    OFF = "off"
    TRACK = "track"
    QUEUE = "queue"


class UnknownItemError(Exception):
    """Le morceau visé n'est plus dans la file."""


class QueueFullError(Exception):
    """La file est pleine."""


def is_video_id(value: str) -> bool:
    """Indique si la valeur a la forme d'un identifiant de vidéo."""
    return _VIDEO_ID.fullmatch(value) is not None


def video_id_from_link(text: str) -> str | None:
    """Identifiant de la vidéo désignée par un lien collé, ``None`` si ce n'en est pas un."""
    candidate = text.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    try:
        parts = urlsplit(candidate)
        host = (parts.hostname or "").lower()
    except ValueError:
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    found = ""
    if host == _SHORT_HOST and segments:
        found = segments[0]
    elif host in _WATCH_HOSTS:
        if segments == ["watch"]:
            found = parse_qs(parts.query).get("v", [""])[0]
        elif len(segments) == 2 and segments[0] in _PATH_PREFIXES:
            found = segments[1]
    return found if is_video_id(found) else None


def duration_seconds(iso_duration: str) -> int:
    """Durée en secondes d'une valeur ISO 8601 (``PT4M13S``) ; 0 pour un direct ou l'inconnu."""
    match = _DURATION.fullmatch(iso_duration)
    if match is None:
        return 0
    days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


class MusicDeck:
    """Lecture commune : morceau en cours, file d'attente et boucle.

    Le serveur fait foi sur la position : elle se calcule depuis l'heure de
    lancement, sans dépendre du lecteur d'un participant.
    """

    def __init__(self) -> None:
        self.current: QueueItem | None = None
        self.queue: list[QueueItem] = []
        self.repeat = RepeatMode.OFF
        # Change à chaque lancement, même du même morceau : il distingue deux lectures.
        self.play_id = 0
        # Vidéo affichée en grand ; chaque nouveau morceau repart en musique seule.
        self.video_shown = False
        self._paused = False
        self._offset = 0.0
        self._started_at = 0.0

    @property
    def is_playing(self) -> bool:
        return self.current is not None and not self._paused

    def position(self, now: float) -> float:
        """Position de lecture en secondes, bornée à la durée du morceau."""
        if self.current is None:
            return 0.0
        elapsed = 0.0 if self._paused else now - self._started_at
        return min(max(self._offset + elapsed, 0.0), float(self.current.track.duration_seconds))

    def remaining(self, now: float) -> float | None:
        """Secondes avant la fin du morceau, ``None`` si rien n'est en lecture."""
        if self.current is None or self._paused:
            return None
        return self.current.track.duration_seconds - self.position(now)

    def play(self, track: Track, now: float, show_video: bool = False) -> None:
        """Joue un morceau tout de suite, avec ou sans sa vidéo ; la file ne change pas."""
        self._start(QueueItem(uuid4(), track), now)
        self.video_shown = show_video

    def show_video(self, shown: bool) -> None:
        """Affiche ou range la vidéo du morceau en cours."""
        self.video_shown = shown and self.current is not None

    def play_all(self, tracks: Sequence[Track], now: float) -> None:
        """Remplace la lecture et la file par une suite de morceaux."""
        items = [QueueItem(uuid4(), track) for track in tracks[: QUEUE_MAX + 1]]
        if not items:
            return
        self.queue = items[1:]
        self._start(items[0], now)

    def play_item(self, item_id: UUID, now: float) -> None:
        """Joue tout de suite un morceau de la file, qui en sort."""
        item = self._item(item_id)
        self.queue.remove(item)
        self._start(item, now)

    def enqueue(self, track: Track, now: float) -> None:
        """Ajoute un morceau en fin de file ; il démarre si rien n'est en cours."""
        if self.current is None:
            self.play(track, now)
            return
        if len(self.queue) >= QUEUE_MAX:
            raise QueueFullError
        self.queue.append(QueueItem(uuid4(), track))

    def remove(self, item_id: UUID) -> None:
        """Retire un morceau de la file."""
        self.queue.remove(self._item(item_id))

    def move(self, item_id: UUID, index: int) -> None:
        """Déplace un morceau dans la file ; l'index est borné à la file."""
        item = self._item(item_id)
        self.queue.remove(item)
        self.queue.insert(min(max(index, 0), len(self.queue)), item)

    def clear_queue(self) -> None:
        """Vide la file sans arrêter le morceau en cours."""
        self.queue = []

    def pause(self, now: float) -> None:
        if self.is_playing:
            self._offset = self.position(now)
            self._paused = True

    def resume(self, now: float) -> None:
        if self.current is not None and self._paused:
            self._paused = False
            self._started_at = now

    def seek(self, seconds: float, now: float) -> None:
        """Place la lecture à une position, bornée à la durée du morceau."""
        if self.current is not None:
            duration = float(self.current.track.duration_seconds)
            self._offset = min(max(seconds, 0.0), duration)
            self._started_at = now

    def skip(self, now: float) -> None:
        """Passe au morceau suivant, sans tenir compte de la boucle sur un morceau."""
        finished = self.current
        if finished is not None and self.repeat is RepeatMode.QUEUE:
            self.queue.append(finished)
        if self.queue:
            self._start(self.queue.pop(0), now)
        else:
            self.stop()

    def finish(self, now: float) -> None:
        """Enchaîne à la fin naturelle du morceau, selon la boucle choisie."""
        if self.current is not None and self.repeat is RepeatMode.TRACK:
            shown = self.video_shown
            self._start(self.current, now)
            self.video_shown = shown
        else:
            self.skip(now)

    def stop(self) -> None:
        """Arrête la musique ; la file est conservée."""
        self.current = None
        self.video_shown = False
        self._paused = False
        self._offset = 0.0

    def _start(self, item: QueueItem, now: float) -> None:
        self.current = item
        self.play_id += 1
        self.video_shown = False
        self._paused = False
        self._offset = 0.0
        self._started_at = now

    def _item(self, item_id: UUID) -> QueueItem:
        item = next((entry for entry in self.queue if entry.id == item_id), None)
        if item is None:
            raise UnknownItemError
        return item
