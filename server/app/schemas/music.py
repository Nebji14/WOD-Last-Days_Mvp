"""Modèles d'entrée et de sortie de la musique (lecture, file et playlists)."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.music import (
    PLAYLIST_NAME_MAX,
    QUEUE_MAX,
    Playlist,
    PlaylistTrack,
    QueueItem,
    RepeatMode,
    Track,
)
from app.services.music import DeckState, NowPlaying

VideoId = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{11}$")]

_MAX_SECONDS = 86400.0


class TrackResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    duration_seconds: int

    @classmethod
    def from_track(cls, track: Track) -> "TrackResponse":
        return cls(
            video_id=track.video_id,
            title=track.title,
            channel=track.channel,
            duration_seconds=track.duration_seconds,
        )


class SearchResponse(BaseModel):
    tracks: list[TrackResponse]


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class NowPlayingResponse(BaseModel):
    """Lecture en cours, envoyée à tous. La file du MJ n'y figure pas."""

    play_id: int
    track: TrackResponse | None
    playing: bool
    position: float
    video_shown: bool

    @classmethod
    def from_now(cls, now: NowPlaying) -> "NowPlayingResponse":
        return cls(
            play_id=now.play_id,
            track=TrackResponse.from_track(now.track) if now.track else None,
            playing=now.playing,
            position=now.position,
            video_shown=now.video_shown,
        )


class ListedTrackResponse(BaseModel):
    """Morceau d'une file ou d'une playlist, avec son identifiant propre."""

    id: UUID
    track: TrackResponse

    @classmethod
    def from_entry(cls, entry: QueueItem | PlaylistTrack) -> "ListedTrackResponse":
        return cls(id=entry.id, track=TrackResponse.from_track(entry.track))


class DeckResponse(BaseModel):
    """État complet, réservé au MJ."""

    now: NowPlayingResponse
    queue: list[ListedTrackResponse]
    repeat: RepeatMode

    @classmethod
    def from_deck(cls, deck: DeckState) -> "DeckResponse":
        return cls(
            now=NowPlayingResponse.from_now(deck.now),
            queue=[ListedTrackResponse.from_entry(item) for item in deck.queue],
            repeat=deck.repeat,
        )


class PlaylistResponse(BaseModel):
    id: UUID
    name: str
    tracks: list[ListedTrackResponse]

    @classmethod
    def from_playlist(cls, playlist: Playlist) -> "PlaylistResponse":
        return cls(
            id=playlist.id,
            name=playlist.name,
            tracks=[ListedTrackResponse.from_entry(entry) for entry in playlist.tracks],
        )


class PlaylistsResponse(BaseModel):
    playlists: list[PlaylistResponse]


class TrackRequest(BaseModel):
    video_id: VideoId


class PlayRequest(TrackRequest):
    show_video: bool = False


class VideoRequest(BaseModel):
    shown: bool


class MoveItemRequest(BaseModel):
    index: int = Field(ge=0, le=QUEUE_MAX)


class SkipRequest(BaseModel):
    """Lecture que le MJ veut passer."""

    play_id: int = Field(ge=0)


class SeekRequest(BaseModel):
    seconds: float = Field(ge=0, le=_MAX_SECONDS, allow_inf_nan=False)


class RepeatRequest(BaseModel):
    mode: RepeatMode


class PlaylistNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=PLAYLIST_NAME_MAX)


class PlayPlaylistRequest(BaseModel):
    shuffled: bool = False


class PlaylistCreatedResponse(BaseModel):
    id: UUID
