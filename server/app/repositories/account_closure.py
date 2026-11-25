"""Désactivation, réactivation et suppression définitive d'un compte joueur.

L'annonce du départ est écrite dans la même transaction : elle n'existe que si
le départ a bien eu lieu.
"""

from dataclasses import dataclass
from uuid import UUID, uuid4

import asyncpg

from app.domain.chat import Notice


@dataclass(frozen=True, slots=True)
class DeletedAccount:
    """Trace d'une suppression définitive.

    Attributs:
        message_id: annonce publiée dans le chat.
        portraits: fichiers des photos à effacer du stockage.
    """

    message_id: UUID
    portraits: list[str]


class PgAccountClosureRepository:
    """Dépôt des départs sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def disable(self, account_id: UUID, body: str) -> UUID | None:
        """Désactive un compte joueur et annonce son départ.

        Returns:
            L'annonce publiée, ou ``None`` si le compte n'est plus actif.
        """
        async with self._pool.acquire() as connection, connection.transaction():
            updated = await connection.fetchval(
                """
                update account set status = 'disabled'
                where id = $1 and role = 'player' and status = 'active'
                returning id
                """,
                account_id,
            )
            if updated is None:
                return None
            return await _insert_notice(connection, account_id, body, Notice.DISABLED)

    async def reactivate(self, account_id: UUID) -> bool:
        """Rend son accès à un joueur désactivé ; ``False`` s'il ne l'est pas."""
        updated = await self._pool.fetchval(
            """
            update account set status = 'active'
            where id = $1 and role = 'player' and status = 'disabled'
            returning id
            """,
            account_id,
        )
        return updated is not None

    async def delete(self, account_id: UUID, body: str) -> DeletedAccount | None:
        """Efface un compte joueur, ses personnages et tout ce qui s'y rattache.

        Ses messages restent, sans auteur. Les tactiques qu'aucune feuille ne
        connaît plus sont supprimées.

        Returns:
            La trace de la suppression, ou ``None`` si le compte n'existe plus.
        """
        async with self._pool.acquire() as connection, connection.transaction():
            locked = await connection.fetchval(
                "select id from account where id = $1 and role = 'player' for update", account_id
            )
            if locked is None:
                return None
            message_id = await _insert_notice(connection, account_id, body, Notice.DELETED)
            rows = await connection.fetch(
                """
                select s.portrait_path
                from character_sheet s join character c on c.id = s.character_id
                where c.owner_id = $1 and s.portrait_path is not null
                """,
                account_id,
            )
            await connection.execute("delete from character where owner_id = $1", account_id)
            await connection.execute(
                "delete from tactic t where not exists "
                "(select 1 from sheet_tactic st where st.tactic_id = t.id)"
            )
            await connection.execute("delete from account where id = $1", account_id)
        return DeletedAccount(message_id, [row["portrait_path"] for row in rows])


async def _insert_notice(
    connection: asyncpg.Connection, account_id: UUID, body: str, notice: Notice
) -> UUID:
    message_id: UUID = await connection.fetchval(
        """
        insert into chat_message (author_id, client_token, body, notice)
        values ($1, $2, $3, $4)
        returning id
        """,
        account_id,
        uuid4(),
        body,
        notice.value,
    )
    return message_id
