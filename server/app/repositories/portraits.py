"""Accès aux photos des formes et du compte du MJ (colonnes ``portrait_path``)."""

from dataclasses import dataclass
from uuid import UUID

import asyncpg

from app.domain.portraits import PortraitOwner


@dataclass(frozen=True, slots=True)
class PortraitChange:
    """Portrait remplacé : fichier précédent, ``None`` s'il n'y en avait pas."""

    previous: str | None


class PgPortraitRepository:
    """Dépôt des portraits sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def set_portrait(self, sheet_id: UUID, path: str | None) -> PortraitChange | None:
        """Change le portrait d'une forme ; ``None`` si la forme n'existe plus.

        La ligne est verrouillée : deux envois simultanés rendent chacun le
        fichier qu'ils ont réellement remplacé.
        """
        row = await self._pool.fetchrow(
            """
            with locked as (
                select id, portrait_path from character_sheet where id = $1 for update
            )
            update character_sheet s set portrait_path = $2
            from locked l where s.id = l.id
            returning l.portrait_path as previous
            """,
            sheet_id,
            path,
        )
        return PortraitChange(row["previous"]) if row else None

    async def set_account_portrait(
        self, account_id: UUID, path: str | None
    ) -> PortraitChange | None:
        """Change la photo d'un compte, avec le même verrou."""
        row = await self._pool.fetchrow(
            """
            with locked as (
                select id, portrait_path from account where id = $1 for update
            )
            update account a set portrait_path = $2
            from locked l where a.id = l.id
            returning l.portrait_path as previous
            """,
            account_id,
            path,
        )
        return PortraitChange(row["previous"]) if row else None

    async def owner_of(self, path: str) -> PortraitOwner | None:
        """Retourne à qui appartient ce portrait, ou ``None``.

        La photo d'un compte est visible de toute la table, comme un personnage joué.
        """
        row = await self._pool.fetchrow(
            """
            select c.owner_id, s.is_main,
                   coalesce(a.played_character_id = c.id, false) as is_played
            from character_sheet s
            join character c on c.id = s.character_id
            left join account a on a.id = c.owner_id
            where s.portrait_path = $1
            union all
            select a.id, true, true from account a where a.portrait_path = $1
            """,
            path,
        )
        return PortraitOwner(row["owner_id"], row["is_main"], row["is_played"]) if row else None
