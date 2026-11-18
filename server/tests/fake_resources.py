"""Doublure du dépôt des ressources, construite sur les personnages en mémoire."""

from dataclasses import replace
from uuid import UUID, uuid4

from app.domain.character import Character, Entry
from app.domain.resources import Resource, ResourceField
from tests.fake_characters import FakeCharacterStore


class FakeResourceStore:
    """Ressources rangées dans les personnages de ``FakeCharacterStore``."""

    def __init__(self, characters: FakeCharacterStore) -> None:
        self._characters = characters

    def _holder(self, resource_id: UUID) -> Character | None:
        return next(
            (c for c in self._characters.characters() if c.resource(resource_id) is not None),
            None,
        )

    async def resource_owner(self, resource_id: UUID) -> UUID | None:
        holder = self._holder(resource_id)
        return None if holder is None else holder.id

    async def add_resource(self, character_id: UUID, name: str, max_value: int) -> None:
        character = await self._characters.get(character_id)
        assert character is not None
        resource = Resource(uuid4(), name, max_value, max_value)
        self._characters.put(replace(character, resources=[*character.resources, resource]))

    async def update_resource(
        self, resource_id: UUID, field: ResourceField, value: str | int, expected: str | int
    ) -> bool:
        character = self._holder(resource_id)
        resource = None if character is None else character.resource(resource_id)
        if character is None or resource is None or getattr(resource, field.value) != expected:
            return False
        if field is ResourceField.NAME:
            changed = replace(resource, name=str(value))
        elif field is ResourceField.MAX:
            maximum = int(value)
            changed = replace(
                resource, max_value=maximum, current_value=min(resource.current_value, maximum)
            )
        else:
            changed = replace(resource, current_value=int(value))
        resources = [changed if r.id == resource_id else r for r in character.resources]
        self._characters.put(replace(character, resources=resources))
        return True

    async def delete_resource(self, character_id: UUID, resource_id: UUID) -> None:
        character = await self._characters.get(character_id)
        assert character is not None
        sheets = [
            replace(sheet, entries=[_without_resource(e, resource_id) for e in sheet.entries])
            for sheet in character.sheets
        ]
        resources = [r for r in character.resources if r.id != resource_id]
        self._characters.put(replace(character, sheets=sheets, resources=resources))


def _without_resource(entry: Entry, resource_id: UUID) -> Entry:
    """Retire de la recette le coût dans la ressource supprimée."""
    if entry.roll is None or entry.roll.get("resource_id") != str(resource_id):
        return entry
    return replace(entry, roll=entry.roll | {"resource_id": None, "resource_cost": 0})
