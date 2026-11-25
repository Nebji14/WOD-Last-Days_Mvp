"""Playlists du MJ : création, lecture, modification et suppression.

Le droit d'accès (MJ uniquement) est contrôlé par les routes.
"""

from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.music import PLAYLIST_NAME_MAX, PLAYLIST_TRACKS_MAX, Playlist, Track
from app.domain.names import clean_name


class PlaylistStore(Protocol):
    """Accès aux playlists attendu par le service."""

    async def list_playlists(self) -> list[Playlist]: ...
    async def get(self, playlist_id: UUID) -> Playlist | None: ...
    async def create(self, name: str) -> UUID: ...
    async def rename(self, playlist_id: UUID, name: str) -> bool: ...
    async def delete(self, playlist_id: UUID) -> bool: ...
    async def add_track(self, playlist_id: UUID, track: Track) -> bool: ...
    async def remove_track(self, playlist_id: UUID, entry_id: UUID) -> bool: ...


class PlaylistBroadcaster(Protocol):
    """Signal temps réel d'un changement des playlists."""

    async def playlists_changed(self) -> None: ...


def _not_found() -> AppError:
    return AppError(ErrorCode.NOT_FOUND, "Élément introuvable.", status_code=404)


class PlaylistService:
    """Cas d'usage des playlists.

    Args:
        store: accès aux données.
        broadcaster: signal temps réel vers l'outil du MJ.
    """

    def __init__(self, store: PlaylistStore, broadcaster: PlaylistBroadcaster) -> None:
        self._store = store
        self._broadcaster = broadcaster

    async def list_playlists(self) -> list[Playlist]:
        """Retourne toutes les playlists avec leurs morceaux."""
        return await self._store.list_playlists()

    async def get(self, playlist_id: UUID) -> Playlist:
        """Retourne une playlist."""
        playlist = await self._store.get(playlist_id)
        if playlist is None:
            raise _not_found()
        return playlist

    async def create(self, name: str) -> UUID:
        """Crée une playlist vide."""
        playlist_id = await self._store.create(self._name(name))
        await self._broadcaster.playlists_changed()
        return playlist_id

    async def rename(self, playlist_id: UUID, name: str) -> None:
        """Renomme une playlist."""
        if not await self._store.rename(playlist_id, self._name(name)):
            raise _not_found()
        await self._broadcaster.playlists_changed()

    async def delete(self, playlist_id: UUID) -> None:
        """Supprime une playlist et ses morceaux ; la lecture en cours continue."""
        if not await self._store.delete(playlist_id):
            raise _not_found()
        await self._broadcaster.playlists_changed()

    async def add_track(self, playlist_id: UUID, track: Track) -> None:
        """Ajoute un morceau en fin de playlist."""
        playlist = await self.get(playlist_id)
        if len(playlist.tracks) >= PLAYLIST_TRACKS_MAX:
            raise AppError(ErrorCode.MUSIC_LIST_FULL, "Playlist pleine.", status_code=422)
        if not await self._store.add_track(playlist_id, track):
            raise _not_found()
        await self._broadcaster.playlists_changed()

    async def remove_track(self, playlist_id: UUID, entry_id: UUID) -> None:
        """Retire un morceau d'une playlist."""
        if not await self._store.remove_track(playlist_id, entry_id):
            raise _not_found()
        await self._broadcaster.playlists_changed()

    @staticmethod
    def _name(name: str) -> str:
        cleaned = clean_name(name, PLAYLIST_NAME_MAX)
        if cleaned is None:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Nom vide ou trop long.", status_code=422)
        return cleaned
