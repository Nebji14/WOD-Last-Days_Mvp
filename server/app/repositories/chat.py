"""Accès aux données du chat général (table ``chat_message``)."""

import json
from typing import Any
from uuid import UUID

import asyncpg

from app.domain.accounts import Role
from app.domain.chat import ChatMessage, Notice

_SELECT = """
    select m.id, m.position, m.author_id, coalesce(a.display_name, '') as author_name,
           coalesce(a.role, 'player') as author_role, m.body, m.sent_at, m.edited_at,
           m.deleted_at, d.role as deleted_by_role, m.roll, m.notice
    from chat_message m
    left join account a on a.id = m.author_id
    left join account d on d.id = m.deleted_by
"""


class PgChatRepository:
    """Dépôt des messages sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, message_id: UUID) -> ChatMessage | None:
        """Retourne le message portant cet identifiant, ou ``None``."""
        row = await self._pool.fetchrow(f"{_SELECT} where m.id = $1", message_id)
        return _to_message(row) if row else None

    async def list_page(self, before: int | None, limit: int) -> list[ChatMessage]:
        """Retourne une page d'historique, du plus récent au plus ancien.

        Args:
            before: ne retourner que les messages de position strictement
                inférieure ; ``None`` pour partir des plus récents.
            limit: nombre maximal de messages.
        """
        rows = await self._pool.fetch(
            f"""
            {_SELECT}
            where $1::bigint is null or m.position < $1
            order by m.position desc
            limit $2
            """,
            before,
            limit,
        )
        return [_to_message(row) for row in rows]

    async def create(
        self, author_id: UUID, client_token: UUID, body: str, roll: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Enregistre un message, ou le résultat d'un jet de dés avec son détail.

        L'envoi est idempotent : si l'auteur a déjà envoyé un message avec ce
        jeton, le message existant est retourné sans en créer un second.
        """
        async with self._pool.acquire() as connection:
            message_id = await connection.fetchval(
                """
                insert into chat_message (author_id, client_token, body, roll)
                values ($1, $2, $3, $4::jsonb)
                on conflict (author_id, client_token) do nothing
                returning id
                """,
                author_id,
                client_token,
                body,
                None if roll is None else json.dumps(roll),
            )
            if message_id is None:
                message_id = await connection.fetchval(
                    "select id from chat_message where author_id = $1 and client_token = $2",
                    author_id,
                    client_token,
                )
            row = await connection.fetchrow(f"{_SELECT} where m.id = $1", message_id)
        return _to_message(row)

    async def update_body(self, message_id: UUID, body: str) -> ChatMessage | None:
        """Remplace le texte d'un message et date la modification.

        Returns:
            Le message modifié, ou ``None`` s'il n'existe pas ou s'il est supprimé.
        """
        updated = await self._pool.fetchval(
            """
            update chat_message set body = $2, edited_at = now()
            where id = $1 and deleted_at is null
            returning id
            """,
            message_id,
            body,
        )
        return await self.get(message_id) if updated else None

    async def mark_deleted(self, message_id: UUID, deleted_by: UUID) -> ChatMessage | None:
        """Efface le texte d'un message et conserve la trace de sa suppression.

        Returns:
            Le message supprimé, ou ``None`` s'il n'existe pas ou s'il l'était déjà.
        """
        updated = await self._pool.fetchval(
            """
            update chat_message set body = null, deleted_at = now(), deleted_by = $2
            where id = $1 and deleted_at is null
            returning id
            """,
            message_id,
            deleted_by,
        )
        return await self.get(message_id) if updated else None


def _to_message(row: asyncpg.Record) -> ChatMessage:
    """Convertit une ligne de la requête en objet du domaine."""
    # Le compte qui a supprimé un message peut avoir disparu : la date en fait foi.
    deleted_by_role = row["deleted_by_role"] or (Role.PLAYER if row["deleted_at"] else None)
    return ChatMessage(
        id=row["id"],
        position=row["position"],
        author_id=row["author_id"],
        author_name=row["author_name"],
        author_role=Role(row["author_role"]),
        body=row["body"],
        sent_at=row["sent_at"],
        edited_at=row["edited_at"],
        deleted_by_role=Role(deleted_by_role) if deleted_by_role else None,
        roll=json.loads(row["roll"]) if row["roll"] else None,
        notice=Notice(row["notice"]) if row["notice"] else None,
    )
