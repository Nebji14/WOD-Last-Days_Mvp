"""Accès aux ressources libres des personnages (table ``character_resource``)."""

from uuid import UUID

import asyncpg

from app.domain.resources import ResourceField

# Baisser le maximum ramène la valeur disponible sous ce nouveau maximum.
_UPDATES = {
    ResourceField.NAME: "name = $2",
    ResourceField.MAX: "max_value = $2, current_value = least(current_value, $2)",
    ResourceField.CURRENT: "current_value = $2",
}


class PgResourceRepository:
    """Dépôt des ressources sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def resource_owner(self, resource_id: UUID) -> UUID | None:
        """Personnage qui porte la ressource, ou ``None`` si elle n'existe pas."""
        character_id: UUID | None = await self._pool.fetchval(
            "select character_id from character_resource where id = $1", resource_id
        )
        return character_id

    async def add_resource(self, character_id: UUID, name: str, max_value: int) -> None:
        """Crée une ressource pleine : la valeur disponible part du maximum."""
        await self._pool.execute(
            "insert into character_resource (character_id, name, max_value, current_value) "
            "values ($1, $2, $3, $3)",
            character_id,
            name,
            max_value,
        )

    async def update_resource(
        self, resource_id: UUID, field: ResourceField, value: str | int, expected: str | int
    ) -> bool:
        """Modifie un champ si sa valeur est encore ``expected`` ; ``False`` sinon."""
        updated = await self._pool.fetchval(
            f"update character_resource set {_UPDATES[field]} "  # noqa: S608
            f"where id = $1 and {field.value} = $3 returning id",
            resource_id,
            value,
            expected,
        )
        return updated is not None

    async def delete_resource(self, character_id: UUID, resource_id: UUID) -> None:
        """Supprime la ressource et retire son coût des recettes qui la dépensaient."""
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "update sheet_entry e "
                "set roll = e.roll || jsonb_build_object('resource_id', null, 'resource_cost', 0) "
                "from character_sheet s "
                "where s.id = e.sheet_id and s.character_id = $1 "
                "and e.roll ->> 'resource_id' = $2",
                character_id,
                str(resource_id),
            )
            await connection.execute("delete from character_resource where id = $1", resource_id)
