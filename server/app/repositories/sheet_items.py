"""Accès aux éléments rattachés à une feuille ou à un personnage.

Spécialités, annotations de moralité, éléments de feuille (atouts, armes…),
tactiques, dépenses d'expérience et notes.
"""

from collections.abc import Sequence
from dataclasses import astuple, dataclass
from enum import StrEnum
from uuid import UUID

import asyncpg

from app.domain.character import EntryKind, Tactic


class ItemKind(StrEnum):
    """Type d'élément dont on cherche le personnage."""

    SHEET = "sheet"
    ENTRY = "entry"
    MORALITY_NOTE = "morality_note"
    EXPENSE = "expense"
    NOTE = "note"


_OWNER_QUERIES = {
    ItemKind.SHEET: "select character_id from character_sheet where id = $1",
    ItemKind.ENTRY: (
        "select s.character_id from sheet_entry e "
        "join character_sheet s on s.id = e.sheet_id where e.id = $1"
    ),
    ItemKind.MORALITY_NOTE: (
        "select s.character_id from morality_note m "
        "join character_sheet s on s.id = m.sheet_id where m.id = $1"
    ),
    ItemKind.EXPENSE: "select character_id from xp_expense where id = $1",
    ItemKind.NOTE: "select character_id from character_note where id = $1",
}


@dataclass(frozen=True, slots=True)
class EntryValues:
    """Valeurs d'un élément de feuille, dans l'ordre des colonnes de ``sheet_entry``."""

    name: str
    description: str
    level: int | None
    quantity: int | None
    damage_modifier: int | None
    range: str | None
    size: int | None
    initiative_penalty: int | None
    general_protection: int | None
    ballistic_protection: int | None
    min_strength: int | None
    defense_penalty: int | None


_ENTRY_COLUMNS = (
    "name, description, level, quantity, damage_modifier, range, size, initiative_penalty, "
    "general_protection, ballistic_protection, min_strength, defense_penalty"
)


class PgSheetItemRepository:
    """Dépôt des éléments de feuille sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def character_id_of(self, kind: ItemKind, item_id: UUID) -> UUID | None:
        """Retourne le personnage auquel se rattache un élément, ou ``None`` s'il n'existe pas."""
        character_id: UUID | None = await self._pool.fetchval(_OWNER_QUERIES[kind], item_id)
        return character_id

    async def replace_specialties(self, sheet_id: UUID, skill: str, labels: Sequence[str]) -> None:
        """Remplace les spécialités d'une compétence (05-I9). Une liste vide les supprime."""
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "delete from sheet_specialty where sheet_id = $1 and skill = $2", sheet_id, skill
            )
            await connection.executemany(
                "insert into sheet_specialty (sheet_id, skill, label, position) "
                "values ($1, $2, $3, $4)",
                [(sheet_id, skill, label, position) for position, label in enumerate(labels)],
            )

    async def add_morality_note(self, sheet_id: UUID, level: int, body: str) -> None:
        await self._pool.execute(
            "insert into morality_note (sheet_id, level, body) values ($1, $2, $3)",
            sheet_id,
            level,
            body,
        )

    async def update_morality_note(self, note_id: UUID, level: int, body: str) -> None:
        await self._pool.execute(
            "update morality_note set level = $2, body = $3 where id = $1", note_id, level, body
        )

    async def delete_morality_note(self, note_id: UUID) -> None:
        await self._pool.execute("delete from morality_note where id = $1", note_id)

    async def add_entry(self, sheet_id: UUID, kind: EntryKind, values: EntryValues) -> None:
        await self._pool.execute(
            f"insert into sheet_entry (sheet_id, kind, {_ENTRY_COLUMNS}) "  # noqa: S608
            "values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)",
            sheet_id,
            kind.value,
            *astuple(values),
        )

    async def get_entry_kind(self, entry_id: UUID) -> EntryKind | None:
        kind = await self._pool.fetchval("select kind from sheet_entry where id = $1", entry_id)
        return EntryKind(kind) if kind else None

    async def update_entry(self, entry_id: UUID, values: EntryValues) -> None:
        await self._pool.execute(
            f"update sheet_entry set ({_ENTRY_COLUMNS}) = "  # noqa: S608
            "($2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) where id = $1",
            entry_id,
            *astuple(values),
        )

    async def delete_entry(self, entry_id: UUID) -> None:
        await self._pool.execute("delete from sheet_entry where id = $1", entry_id)

    async def list_tactics(self) -> list[Tactic]:
        """Retourne toutes les tactiques existantes, pour en rattacher une à une feuille (Q05-3)."""
        rows = await self._pool.fetch(
            "select id, name, description from tactic order by lower(name), created_at"
        )
        return [Tactic(row["id"], row["name"], row["description"]) for row in rows]

    async def tactic_exists(self, tactic_id: UUID) -> bool:
        return bool(await self._pool.fetchval("select true from tactic where id = $1", tactic_id))

    async def create_tactic(self, sheet_id: UUID, name: str, description: str) -> None:
        """Crée une tactique et la rattache à la feuille."""
        async with self._pool.acquire() as connection, connection.transaction():
            tactic_id = await connection.fetchval(
                "insert into tactic (name, description) values ($1, $2) returning id",
                name,
                description,
            )
            await connection.execute(
                "insert into sheet_tactic (sheet_id, tactic_id) values ($1, $2)",
                sheet_id,
                tactic_id,
            )

    async def link_tactic(self, sheet_id: UUID, tactic_id: UUID) -> None:
        """Rattache une tactique existante à la feuille. Sans effet si elle l'est déjà."""
        await self._pool.execute(
            "insert into sheet_tactic (sheet_id, tactic_id) values ($1, $2) on conflict do nothing",
            sheet_id,
            tactic_id,
        )

    async def is_tactic_linked(self, sheet_id: UUID, tactic_id: UUID) -> bool:
        return bool(
            await self._pool.fetchval(
                "select true from sheet_tactic where sheet_id = $1 and tactic_id = $2",
                sheet_id,
                tactic_id,
            )
        )

    async def update_tactic(self, tactic_id: UUID, name: str, description: str) -> list[UUID]:
        """Modifie une tactique partagée.

        Returns:
            Les personnages dont une feuille connaît cette tactique.
        """
        await self._pool.execute(
            "update tactic set name = $2, description = $3 where id = $1",
            tactic_id,
            name,
            description,
        )
        rows = await self._pool.fetch(
            "select distinct s.character_id from sheet_tactic st "
            "join character_sheet s on s.id = st.sheet_id where st.tactic_id = $1",
            tactic_id,
        )
        return [row["character_id"] for row in rows]

    async def unlink_tactic(self, sheet_id: UUID, tactic_id: UUID) -> None:
        """Détache une tactique de la feuille ; la supprime si plus aucune ne la connaît (C06)."""
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "delete from sheet_tactic where sheet_id = $1 and tactic_id = $2",
                sheet_id,
                tactic_id,
            )
            await connection.execute(
                "delete from tactic t where t.id = $1 and not exists "
                "(select 1 from sheet_tactic st where st.tactic_id = t.id)",
                tactic_id,
            )

    async def add_expense(
        self, character_id: UUID, is_tactical: bool, points: int, justification: str
    ) -> None:
        await self._pool.execute(
            "insert into xp_expense (character_id, is_tactical, points, justification) "
            "values ($1, $2, $3, $4)",
            character_id,
            is_tactical,
            points,
            justification,
        )

    async def update_expense(self, expense_id: UUID, points: int, justification: str) -> None:
        await self._pool.execute(
            "update xp_expense set points = $2, justification = $3 where id = $1",
            expense_id,
            points,
            justification,
        )

    async def delete_expense(self, expense_id: UUID) -> None:
        await self._pool.execute("delete from xp_expense where id = $1", expense_id)

    async def add_note(self, character_id: UUID, title: str, body: str) -> UUID:
        note_id: UUID = await self._pool.fetchval(
            "insert into character_note (character_id, title, body) values ($1, $2, $3) "
            "returning id",
            character_id,
            title,
            body,
        )
        return note_id

    async def update_note(self, note_id: UUID, title: str, body: str) -> None:
        await self._pool.execute(
            "update character_note set title = $2, body = $3, updated_at = now() where id = $1",
            note_id,
            title,
            body,
        )

    async def delete_note(self, note_id: UUID) -> None:
        await self._pool.execute("delete from character_note where id = $1", note_id)
