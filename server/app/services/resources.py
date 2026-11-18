"""Cas d'usage des ressources libres d'un personnage (Mana, Douleur…).

Le propriétaire et le MJ les créent, les modifient et les suppriment, sur un
personnage joueur comme sur un PNJ. Chaque écriture prévient les lecteurs de
la fiche.
"""

from typing import Protocol
from uuid import UUID

from app.domain.accounts import Account
from app.domain.character import Character
from app.domain.resources import (
    Resource,
    ResourceField,
    ResourceRuleError,
    check_count,
    check_current,
    check_max,
    clean_name,
)
from app.services.character_access import (
    CharacterAccess,
    edit_conflict,
    not_found,
    rule_violation,
)


class ResourceStore(Protocol):
    """Contrat d'accès aux ressources attendu par le service."""

    async def resource_owner(self, resource_id: UUID) -> UUID | None: ...

    async def add_resource(self, character_id: UUID, name: str, max_value: int) -> None: ...

    async def update_resource(
        self, resource_id: UUID, field: ResourceField, value: str | int, expected: str | int
    ) -> bool: ...

    async def delete_resource(self, character_id: UUID, resource_id: UUID) -> None: ...


def checked_value(
    resource: Resource, others: list[Resource], field: ResourceField, value: str | int
) -> str | int:
    """Valeur à écrire, contrôlée selon le champ.

    Raises:
        ResourceRuleError: pour un type ou une valeur contraire aux règles.
    """
    if field is ResourceField.NAME:
        if not isinstance(value, str):
            raise ResourceRuleError("invalid_type")
        return clean_name(value, others)
    if not isinstance(value, int):
        raise ResourceRuleError("invalid_type")
    if field is ResourceField.MAX:
        check_max(value)
    else:
        check_current(value, resource.max_value)
    return value


class ResourceService:
    """Orchestre les ressources libres.

    Args:
        store: dépôt des ressources.
        access: droits, relecture et diffusion.
    """

    def __init__(self, store: ResourceStore, access: CharacterAccess) -> None:
        self._store = store
        self._access = access

    async def add(
        self, actor: Account, character_id: UUID, name: str, max_value: int
    ) -> Character:
        """Ajoute une ressource, disponible à son maximum.

        Raises:
            AppError: ``not_found`` ou ``rule_violation``.
        """
        character = await self._access.editable(actor, character_id)
        try:
            check_count(len(character.resources))
            cleaned = clean_name(name, character.resources)
            check_max(max_value)
        except ResourceRuleError as error:
            raise rule_violation(str(error), "resource") from None
        await self._store.add_resource(character_id, cleaned, max_value)
        return await self._access.changed(character_id)

    async def update(
        self,
        actor: Account,
        resource_id: UUID,
        field: str,
        value: str | int,
        expected: str | int,
    ) -> Character:
        """Modifie le nom, le maximum ou la valeur disponible d'une ressource.

        Raises:
            AppError: ``not_found``, ``rule_violation`` ou ``edit_conflict``.
        """
        character, resource = await self._resource(actor, resource_id)
        try:
            resource_field = ResourceField(field)
        except ValueError:
            raise rule_violation("unknown_field", field) from None
        others = [other for other in character.resources if other.id != resource_id]
        try:
            checked = checked_value(resource, others, resource_field, value)
        except ResourceRuleError as error:
            raise rule_violation(str(error), field) from None
        if not await self._store.update_resource(resource_id, resource_field, checked, expected):
            raise edit_conflict()
        return await self._access.changed(character.id)

    async def delete(self, actor: Account, resource_id: UUID) -> Character:
        """Supprime une ressource ; les pouvoirs qui la dépensaient n'ont plus ce coût."""
        character, _ = await self._resource(actor, resource_id)
        await self._store.delete_resource(character.id, resource_id)
        return await self._access.changed(character.id)

    async def _resource(self, actor: Account, resource_id: UUID) -> tuple[Character, Resource]:
        owner = await self._store.resource_owner(resource_id)
        character = await self._access.editable(actor, owner)
        resource = character.resource(resource_id)
        if resource is None:
            raise not_found()
        return character, resource
