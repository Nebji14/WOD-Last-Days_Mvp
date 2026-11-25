"""Routes des playlists de musique, réservées au MJ."""

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import ContainerDep, CurrentGm
from app.core.errors import AppError, ErrorCode
from app.schemas.music import (
    PlaylistCreatedResponse,
    PlaylistNameRequest,
    PlaylistResponse,
    PlaylistsResponse,
    PlayPlaylistRequest,
    TrackRequest,
)

_NO_CONTENT = status.HTTP_204_NO_CONTENT

router = APIRouter(prefix="/api/playlists", tags=["music"])


@router.get("")
async def list_playlists(container: ContainerDep, _gm: CurrentGm) -> PlaylistsResponse:
    """Toutes les playlists avec leurs morceaux."""
    playlists = await container.playlist_service.list_playlists()
    return PlaylistsResponse(
        playlists=[PlaylistResponse.from_playlist(playlist) for playlist in playlists]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    payload: PlaylistNameRequest, container: ContainerDep, _gm: CurrentGm
) -> PlaylistCreatedResponse:
    """Crée une playlist vide."""
    return PlaylistCreatedResponse(id=await container.playlist_service.create(payload.name))


@router.patch("/{playlist_id}", status_code=_NO_CONTENT)
async def rename_playlist(
    playlist_id: UUID, payload: PlaylistNameRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Renomme une playlist."""
    await container.playlist_service.rename(playlist_id, payload.name)
    return Response(status_code=_NO_CONTENT)


@router.delete("/{playlist_id}", status_code=_NO_CONTENT)
async def delete_playlist(playlist_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Supprime une playlist."""
    await container.playlist_service.delete(playlist_id)
    return Response(status_code=_NO_CONTENT)


@router.post("/{playlist_id}/tracks", status_code=_NO_CONTENT)
async def add_track(
    playlist_id: UUID, payload: TrackRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Ajoute un morceau en fin de playlist."""
    track = await container.music_catalog.track(payload.video_id)
    await container.playlist_service.add_track(playlist_id, track)
    return Response(status_code=_NO_CONTENT)


@router.delete("/{playlist_id}/tracks/{entry_id}", status_code=_NO_CONTENT)
async def remove_track(
    playlist_id: UUID, entry_id: UUID, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Retire un morceau d'une playlist."""
    await container.playlist_service.remove_track(playlist_id, entry_id)
    return Response(status_code=_NO_CONTENT)


@router.post("/{playlist_id}/play", status_code=_NO_CONTENT)
async def play_playlist(
    playlist_id: UUID, payload: PlayPlaylistRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Diffuse une playlist à toute la table ; elle remplace la file."""
    playlist = await container.playlist_service.get(playlist_id)
    if not playlist.tracks:
        raise AppError(ErrorCode.PLAYLIST_EMPTY, "Playlist vide.", status_code=422)
    tracks = [entry.track for entry in playlist.tracks]
    await container.music_service.play_all(tracks, payload.shuffled)
    return Response(status_code=_NO_CONTENT)
