"""Doublures de la musique : source, playlists et horloge en mémoire."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.music import Playlist, PlaylistTrack, Track
from app.gateways.itunes import SongName, SuggestionSourceError
from app.gateways.youtube import MusicSourceError

HUNT = Track("hunt0000001", "La traque", "Nocturne", 180)
DOCKS = Track("docks000002", "Les docks", "Nocturne", 240)
DAWN = Track("dawn0000003", "L'aube", "Matines", 60)
TIME = SongName("Hans Zimmer", "Time")


class FakeClock:
    """Horloge avancée à la main."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeMusicSource:
    """Source à trois morceaux, qui compte ses appels et peut simuler une panne."""

    def __init__(self) -> None:
        self.tracks = {track.video_id: track for track in (HUNT, DOCKS, DAWN)}
        self.searches: list[str] = []
        self.descriptions: list[str] = []
        self.error: MusicSourceError | None = None

    async def search(self, query: str) -> list[Track]:
        if self.error is not None:
            raise self.error
        self.searches.append(query)
        return [track for track in self.tracks.values() if query in track.title.lower()]

    async def describe(self, video_ids: list[str]) -> list[Track]:
        if self.error is not None:
            raise self.error
        self.descriptions.extend(video_ids)
        return [self.tracks[video_id] for video_id in video_ids if video_id in self.tracks]


class FakeSuggestionSource:
    """Source de suggestions à réponse fixe, qui compte ses appels."""

    def __init__(self) -> None:
        self.queries: list[str] = []
        self.available = True

    async def songs(self, query: str) -> list[SongName]:
        if not self.available:
            raise SuggestionSourceError
        self.queries.append(query)
        return [TIME]


class FakePlaylistStore:
    """Playlists en mémoire."""

    def __init__(self) -> None:
        self.playlists: dict[UUID, Playlist] = {}

    async def list_playlists(self) -> list[Playlist]:
        return sorted(self.playlists.values(), key=lambda p: p.name.lower())

    async def get(self, playlist_id: UUID) -> Playlist | None:
        return self.playlists.get(playlist_id)

    async def create(self, name: str) -> UUID:
        playlist = Playlist(uuid4(), name, datetime(2026, 11, 25, tzinfo=UTC), ())
        self.playlists[playlist.id] = playlist
        return playlist.id

    async def rename(self, playlist_id: UUID, name: str) -> bool:
        if playlist_id not in self.playlists:
            return False
        self.playlists[playlist_id] = replace(self.playlists[playlist_id], name=name)
        return True

    async def delete(self, playlist_id: UUID) -> bool:
        return self.playlists.pop(playlist_id, None) is not None

    async def add_track(self, playlist_id: UUID, track: Track) -> bool:
        playlist = self.playlists.get(playlist_id)
        if playlist is None:
            return False
        tracks = (*playlist.tracks, PlaylistTrack(uuid4(), track))
        self.playlists[playlist_id] = replace(playlist, tracks=tracks)
        return True

    async def remove_track(self, playlist_id: UUID, entry_id: UUID) -> bool:
        playlist = self.playlists.get(playlist_id)
        if playlist is None:
            return False
        tracks = tuple(entry for entry in playlist.tracks if entry.id != entry_id)
        self.playlists[playlist_id] = replace(playlist, tracks=tracks)
        return len(tracks) < len(playlist.tracks)
