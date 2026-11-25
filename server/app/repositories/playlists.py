"""Accès aux données des playlists (``music_playlist`` et ``music_playlist_track``)."""

from uuid import UUID

import asyncpg

from app.domain.music import Playlist, PlaylistTrack, Track

_SELECT = (
    "select p.id, p.name, p.created_at, t.id as entry_id, t.video_id, t.title, t.channel, "
    "t.duration_seconds from music_playlist p "
    "left join music_playlist_track t on t.playlist_id = p.id "
)


class PgPlaylistRepository:
    """Dépôt des playlists sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def list_playlists(self) -> list[Playlist]:
        """Retourne toutes les playlists, par nom, avec leurs morceaux dans l'ordre."""
        rows = await self._pool.fetch(_SELECT + "order by lower(p.name), p.id, t.position")
        return _to_playlists(rows)

    async def get(self, playlist_id: UUID) -> Playlist | None:
        """Retourne une playlist, ou ``None``."""
        rows = await self._pool.fetch(_SELECT + "where p.id = $1 order by t.position", playlist_id)
        playlists = _to_playlists(rows)
        return playlists[0] if playlists else None

    async def create(self, name: str) -> UUID:
        """Crée une playlist vide et retourne son identifiant."""
        playlist_id: UUID = await self._pool.fetchval(
            "insert into music_playlist (name) values ($1) returning id", name
        )
        return playlist_id

    async def rename(self, playlist_id: UUID, name: str) -> bool:
        """Renomme une playlist. Retourne ``False`` si elle n'existe pas."""
        status = await self._pool.execute(
            "update music_playlist set name = $2 where id = $1", playlist_id, name
        )
        return str(status).endswith(" 1")

    async def delete(self, playlist_id: UUID) -> bool:
        """Supprime une playlist et ses morceaux. Retourne ``False`` si elle n'existe pas."""
        status = await self._pool.execute("delete from music_playlist where id = $1", playlist_id)
        return str(status).endswith(" 1")

    async def add_track(self, playlist_id: UUID, track: Track) -> bool:
        """Ajoute un morceau en fin de playlist. Retourne ``False`` si elle n'existe plus."""
        try:
            await self._pool.execute(
                "insert into music_playlist_track "
                "(playlist_id, video_id, title, channel, duration_seconds) "
                "values ($1, $2, $3, $4, $5)",
                playlist_id,
                track.video_id,
                track.title,
                track.channel,
                track.duration_seconds,
            )
        except asyncpg.ForeignKeyViolationError:
            return False
        return True

    async def remove_track(self, playlist_id: UUID, entry_id: UUID) -> bool:
        """Retire un morceau. Retourne ``False`` s'il n'est pas dans cette playlist."""
        status = await self._pool.execute(
            "delete from music_playlist_track where playlist_id = $1 and id = $2",
            playlist_id,
            entry_id,
        )
        return str(status).endswith(" 1")


def _to_playlists(rows: list[asyncpg.Record]) -> list[Playlist]:
    """Regroupe les lignes par playlist, en gardant leur ordre."""
    heads: dict[UUID, asyncpg.Record] = {}
    tracks: dict[UUID, list[PlaylistTrack]] = {}
    for row in rows:
        heads.setdefault(row["id"], row)
        entries = tracks.setdefault(row["id"], [])
        if row["entry_id"] is not None:
            track = Track(row["video_id"], row["title"], row["channel"], row["duration_seconds"])
            entries.append(PlaylistTrack(row["entry_id"], track))
    return [
        Playlist(key, head["name"], head["created_at"], tuple(tracks[key]))
        for key, head in heads.items()
    ]
