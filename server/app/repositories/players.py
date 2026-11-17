"""Lecture des comptes joueurs et de leurs personnages pour l'outil Joueurs (US-025)."""

import asyncpg

from app.domain.accounts import Account, AccountStatus, Role
from app.domain.players import PlayerRecord

_LIST_PLAYERS = """
    select a.id, a.username, a.display_name, a.auth_email, a.role, a.status,
           coalesce(
               array_agg(s.name order by c.created_at, c.id) filter (where s.id is not null),
               '{}'
           ) as character_names
    from account a
    left join character c on c.owner_id = a.id
    left join character_sheet s on s.character_id = c.id and s.is_main
    where a.role = 'player'
    group by a.id
"""


class PgPlayerRepository:
    """Dépôt de lecture des joueurs sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def list_players(self) -> list[PlayerRecord]:
        """Retourne tous les comptes joueurs, avec ou sans personnage (US-025 · CA1)."""
        rows = await self._pool.fetch(_LIST_PLAYERS)
        return [_to_record(row) for row in rows]


def _to_record(row: asyncpg.Record) -> PlayerRecord:
    """Convertit une ligne de la requête en objet du domaine."""
    account = Account(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        auth_email=row["auth_email"],
        role=Role(row["role"]),
        status=AccountStatus(row["status"]),
    )
    return PlayerRecord(account=account, character_names=tuple(row["character_names"]))
