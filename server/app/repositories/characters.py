"""Accès aux données des personnages et de leurs formes.

Tables ``character`` et ``character_sheet``. Les éléments rattachés à une
feuille (spécialités, annotations, atouts, tactiques…) sont dans
``app.repositories.sheet_items``.

Les noms de colonnes insérés dans le SQL viennent tous de listes fermées du
domaine (``SHEET_FIELDS``, ``CHARACTER_FIELDS``) ; les valeurs sont toujours
passées en paramètres.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

import asyncpg

from app.domain.character import Character, SeatCharacter
from app.domain.creation import Specialty
from app.domain.sheet_fields import SHEET_FIELDS
from app.repositories.character_documents import SELECT_DOCUMENT, to_character

CHARACTER_FIELDS = frozenset(
    {"supernatural_level", "supernatural_name", "xp_general_total", "xp_tactical_total"}
)

# Colonnes recopiées quand une forme est créée à partir de la forme principale (Q05-7).
_COPIED_SHEET_COLUMNS = ", ".join([*sorted(SHEET_FIELDS - {"form_name"}), "wound_track"])
_COPIED_ENTRY_COLUMNS = (
    "kind, name, description, level, quantity, damage_modifier, range, size, "
    "initiative_penalty, general_protection, ballistic_protection, min_strength, "
    "defense_penalty, created_at"
)


@dataclass(frozen=True, slots=True)
class NewCharacter:
    """Données d'un personnage à créer (écran 06).

    Attributs:
        values: colonnes de la forme principale et leurs valeurs ; les clés
            appartiennent à ``SHEET_FIELDS``.
    """

    values: Mapping[str, str | int]
    specialties: Sequence[Specialty]


class PgCharacterRepository:
    """Dépôt des personnages sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, character_id: UUID) -> Character | None:
        """Retourne le personnage complet, ou ``None`` s'il n'existe pas."""
        raw = await self._pool.fetchval(f"{SELECT_DOCUMENT} where c.id = $1", character_id)
        return to_character(raw) if raw else None

    async def list_for_owner(self, owner_id: UUID) -> list[Character]:
        """Retourne les personnages d'un compte, du plus ancien au plus récent."""
        rows = await self._pool.fetch(
            f"{SELECT_DOCUMENT} where c.owner_id = $1 order by c.created_at, c.id", owner_id
        )
        return [to_character(row["document"]) for row in rows]

    async def create(self, owner_id: UUID, new: NewCharacter) -> UUID:
        """Crée un personnage, sa forme principale et ses spécialités.

        Le nouveau personnage devient celui joué à la table (Q03-5 : par
        défaut, le dernier créé).

        Returns:
            L'identifiant du personnage créé.
        """
        columns = [name for name in new.values if name in SHEET_FIELDS]
        placeholders = ", ".join(f"${index}" for index in range(2, len(columns) + 2))
        async with self._pool.acquire() as connection, connection.transaction():
            character_id: UUID = await connection.fetchval(
                "insert into character (owner_id) values ($1) returning id", owner_id
            )
            sheet_id = await connection.fetchval(
                f"""
                insert into character_sheet (character_id, is_main, {", ".join(columns)})
                values ($1, true, {placeholders})
                returning id
                """,  # noqa: S608 - colonnes issues de SHEET_FIELDS
                character_id,
                *(new.values[name] for name in columns),
            )
            await connection.executemany(
                "insert into sheet_specialty (sheet_id, skill, label, position) "
                "values ($1, $2, $3, $4)",
                [
                    (sheet_id, specialty.skill, specialty.label, position)
                    for position, specialty in enumerate(new.specialties)
                ],
            )
            await connection.execute(
                "update account set played_character_id = $2 where id = $1",
                owner_id,
                character_id,
            )
        return character_id

    async def delete(self, character_id: UUID) -> None:
        """Supprime définitivement le personnage et tout ce qui s'y rattache (US-010).

        Les tactiques qu'aucune feuille ne connaît plus sont supprimées (C06).
        """
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute("delete from character where id = $1", character_id)
            await connection.execute(
                "delete from tactic t where not exists "
                "(select 1 from sheet_tactic st where st.tactic_id = t.id)"
            )

    async def mark_awakened(self, character_id: UUID) -> None:
        """Enregistre la date de l'éveil, sans toucher à un éveil déjà daté (04a-I5)."""
        await self._pool.execute(
            "update character set awakened_at = now() where id = $1 and awakened_at is null",
            character_id,
        )

    async def set_played(self, owner_id: UUID, character_id: UUID) -> None:
        """Désigne le personnage joué à la table par ce compte (09-I4)."""
        await self._pool.execute(
            "update account set played_character_id = $2 where id = $1", owner_id, character_id
        )

    async def update_character_field(
        self, character_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool:
        """Modifie un champ du personnage si sa valeur est encore ``expected``.

        Returns:
            ``False`` si la valeur a changé entre-temps : rien n'est écrit
            (CDC 12.3, pas d'écrasement silencieux).
        """
        if field not in CHARACTER_FIELDS:
            raise ValueError(field)
        return await self._compare_and_set("character", character_id, field, value, expected)

    async def update_sheet_field(
        self, sheet_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool:
        """Modifie un champ d'une forme si sa valeur est encore ``expected``."""
        if field not in SHEET_FIELDS and field != "wound_track":
            raise ValueError(field)
        return await self._compare_and_set("character_sheet", sheet_id, field, value, expected)

    async def _compare_and_set(
        self, table: str, row_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool:
        updated = await self._pool.fetchval(
            f"update {table} set {field} = $2 where id = $1 and {field} = $3 returning id",  # noqa: S608
            row_id,
            value,
            expected,
        )
        return updated is not None

    async def add_form(self, character_id: UUID, form_name: str) -> UUID:
        """Crée une forme en copiant la forme principale et ses éléments (Q05-7).

        Returns:
            L'identifiant de la nouvelle forme.
        """
        async with self._pool.acquire() as connection, connection.transaction():
            main_id = await connection.fetchval(
                "select id from character_sheet where character_id = $1 and is_main",
                character_id,
            )
            sheet_id: UUID = await connection.fetchval(
                f"""
                insert into character_sheet (character_id, is_main, form_name,
                                             {_COPIED_SHEET_COLUMNS})
                select character_id, false, $2, {_COPIED_SHEET_COLUMNS}
                from character_sheet where id = $1
                returning id
                """,  # noqa: S608
                main_id,
                form_name,
            )
            await connection.execute(
                "insert into sheet_specialty (sheet_id, skill, label, position) "
                "select $2, skill, label, position from sheet_specialty where sheet_id = $1",
                main_id,
                sheet_id,
            )
            await connection.execute(
                "insert into morality_note (sheet_id, level, body, created_at) "
                "select $2, level, body, created_at from morality_note where sheet_id = $1",
                main_id,
                sheet_id,
            )
            await connection.execute(
                f"insert into sheet_entry (sheet_id, {_COPIED_ENTRY_COLUMNS}) "  # noqa: S608
                f"select $2, {_COPIED_ENTRY_COLUMNS} from sheet_entry where sheet_id = $1",
                main_id,
                sheet_id,
            )
            await connection.execute(
                "insert into sheet_tactic (sheet_id, tactic_id) "
                "select $2, tactic_id from sheet_tactic where sheet_id = $1",
                main_id,
                sheet_id,
            )
        return sheet_id

    async def delete_form(self, sheet_id: UUID) -> None:
        """Supprime une forme alternative. La forme principale n'est jamais supprimée."""
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "delete from character_sheet where id = $1 and not is_main", sheet_id
            )
            await connection.execute(
                "delete from tactic t where not exists "
                "(select 1 from sheet_tactic st where st.tactic_id = t.id)"
            )

    async def played_by(self, account_ids: Sequence[UUID]) -> dict[UUID, SeatCharacter]:
        """Retourne, par compte, le résumé du personnage joué à la table.

        Le siège affiche la forme principale (Q05-9). Un compte sans
        personnage joué est absent du résultat.
        """
        rows = await self._pool.fetch(
            """
            select a.id as account_id, c.id as character_id, s.name, s.concept, s.health_max,
                   s.wound_track, s.willpower_max, s.willpower_current
            from account a
            join character c on c.id = a.played_character_id
            join character_sheet s on s.character_id = c.id and s.is_main
            where a.id = any($1::uuid[])
            """,
            list(account_ids),
        )
        return {
            row["account_id"]: SeatCharacter(
                character_id=row["character_id"],
                name=row["name"],
                concept=row["concept"],
                health_max=row["health_max"],
                wound_track=row["wound_track"],
                willpower_max=row["willpower_max"],
                willpower_current=row["willpower_current"],
            )
            for row in rows
        }
