"""Accès aux données des PNJ et de leurs catégories (tables ``npc_profile``, ``npc_category``).

La feuille d'un PNJ vit dans ``character`` et ``character_sheet``, comme celle
d'un personnage joueur ; elle se lit et se modifie par le dépôt des personnages.
"""

from uuid import UUID

import asyncpg

from app.domain.npc_profile import NpcModel
from app.domain.npcs import SIMPLIFIED_TRAITS, NpcCategory, NpcSummary
from app.repositories.character_documents import to_npc_profile
from app.repositories.characters import NewCharacter, insert_main_sheet

_PROFILE_FIELDS = frozenset({"notes", *SIMPLIFIED_TRAITS})

_LIST_NPCS = """
    select c.id, s.id as sheet_id, s.name, s.concept, s.health_max, s.willpower_max,
           s.portrait_path,
           p.model, p.category_id, p.notes, p.power, p.finesse, p.resilience
    from character c
    join npc_profile p on p.character_id = c.id
    join character_sheet s on s.character_id = c.id and s.is_main
    where c.kind = 'npc'
    order by lower(s.name), c.id
"""


class PgNpcRepository:
    """Dépôt des PNJ et des catégories sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    # --- Catégories ------------------------------------------------------

    async def list_categories(self) -> list[NpcCategory]:
        """Retourne toutes les catégories, par nom."""
        rows = await self._pool.fetch(
            "select id, name, parent_id from npc_category order by lower(name), id"
        )
        return [NpcCategory(row["id"], row["name"], row["parent_id"]) for row in rows]

    async def create_category(self, name: str, parent_id: UUID | None) -> UUID:
        """Crée une catégorie et retourne son identifiant."""
        category_id: UUID = await self._pool.fetchval(
            "insert into npc_category (name, parent_id) values ($1, $2) returning id",
            name,
            parent_id,
        )
        return category_id

    async def rename_category(self, category_id: UUID, name: str) -> bool:
        """Renomme une catégorie. Retourne ``False`` si elle n'existe pas."""
        status = await self._pool.execute(
            "update npc_category set name = $2 where id = $1", category_id, name
        )
        return str(status).endswith(" 1")

    async def move_category(self, category_id: UUID, parent_id: UUID | None) -> None:
        """Range une catégorie sous une autre, ou à la racine."""
        await self._pool.execute(
            "update npc_category set parent_id = $2 where id = $1", category_id, parent_id
        )

    async def delete_category(self, category_id: UUID, parent_id: UUID | None) -> None:
        """Supprime une catégorie ; ses PNJ et sous-catégories remontent au parent."""
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "update npc_profile set category_id = $2 where category_id = $1",
                category_id,
                parent_id,
            )
            await connection.execute(
                "update npc_category set parent_id = $2 where parent_id = $1",
                category_id,
                parent_id,
            )
            await connection.execute("delete from npc_category where id = $1", category_id)

    # --- PNJ ---------------------------------------------------------------------------

    async def list_npcs(self) -> list[NpcSummary]:
        """Retourne tous les PNJ, par nom."""
        rows = await self._pool.fetch(_LIST_NPCS)
        return [
            NpcSummary(
                id=row["id"],
                sheet_id=row["sheet_id"],
                name=row["name"],
                concept=row["concept"],
                profile=to_npc_profile(dict(row)),
                health_max=row["health_max"],
                willpower_max=row["willpower_max"],
                portrait=row["portrait_path"],
            )
            for row in rows
        ]

    async def create_npc(
        self,
        model: NpcModel,
        category_id: UUID | None,
        traits: dict[str, int | None],
        new: NewCharacter,
    ) -> UUID:
        """Crée un PNJ sans propriétaire, sa feuille et son profil."""
        async with self._pool.acquire() as connection, connection.transaction():
            character_id: UUID = await connection.fetchval(
                "insert into character (kind, owner_id) values ('npc', null) returning id"
            )
            await insert_main_sheet(connection, character_id, new)
            await connection.execute(
                "insert into npc_profile "
                "(character_id, model, category_id, power, finesse, resilience) "
                "values ($1, $2, $3, $4, $5, $6)",
                character_id,
                model.value,
                category_id,
                traits["power"],
                traits["finesse"],
                traits["resilience"],
            )
        return character_id

    async def update_profile_field(
        self, character_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool:
        """Modifie une donnée propre au PNJ si sa valeur est encore ``expected``.

        Returns:
            ``False`` si la valeur a changé entre-temps : rien n'est écrit
            (pas d'écrasement silencieux).
        """
        if field not in _PROFILE_FIELDS:
            raise ValueError(field)
        status = await self._pool.execute(
            f"update npc_profile set {field} = $2 "  # noqa: S608 - champ de _PROFILE_FIELDS
            f"where character_id = $1 and {field} = $3",
            character_id,
            value,
            expected,
        )
        return str(status).endswith(" 1")

    async def set_category(self, character_id: UUID, category_id: UUID | None) -> None:
        """Range le PNJ dans une catégorie, ou à la racine."""
        await self._pool.execute(
            "update npc_profile set category_id = $2 where character_id = $1",
            character_id,
            category_id,
        )
