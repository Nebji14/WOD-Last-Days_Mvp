"""Paiement d'un jet : Volonté et ressource libre dépensées avant le lancer.

Le coût en Volonté (+3 dés, et coût du pouvoir) et le coût en ressource d'une
recette se cumulent. Tout est vérifié avant la première dépense : un jet trop
cher ne retire rien. Chaque dépense est conditionnelle, pour ne jamais écraser
une modification faite au même moment sur la fiche.
"""

from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.character import Character, Sheet
from app.domain.recipes import RollRecipe
from app.domain.resources import Resource, ResourceField
from app.services.character_access import CharacterAccess, rule_violation


class WillpowerStore(Protocol):
    """Écriture de la volonté disponible."""

    async def update_sheet_field(
        self, sheet_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool: ...


class ResourceSpender(Protocol):
    """Écriture de la valeur disponible d'une ressource."""

    async def update_resource(
        self, resource_id: UUID, field: ResourceField, value: str | int, expected: str | int
    ) -> bool: ...


def _conflict(message: str) -> AppError:
    return AppError(ErrorCode.EDIT_CONFLICT, message, status_code=409)


class RollCosts:
    """Vérifie et dépense ce que coûte un jet.

    Args:
        access: diffusion de la fiche modifiée.
        willpower: écriture de la volonté disponible.
        resources: écriture de la valeur disponible des ressources.
    """

    def __init__(
        self, access: CharacterAccess, willpower: WillpowerStore, resources: ResourceSpender
    ) -> None:
        self._access = access
        self._willpower = willpower
        self._resources = resources

    async def pay(
        self, character: Character, sheet: Sheet, willpower: int, recipe: RollRecipe | None
    ) -> None:
        """Dépense ``willpower`` points de Volonté et le coût en ressource de la recette.

        Raises:
            AppError: ``rule_violation`` si un solde est insuffisant ou si la
                ressource n'existe plus, ``edit_conflict`` si un solde a changé.
        """
        resource = _resource_of(character, recipe)
        cost = recipe.resource_cost if recipe is not None else 0
        if sheet.numbers["willpower_current"] < willpower:
            raise rule_violation("no_willpower", "willpower_current")
        if resource is not None and resource.current_value < cost:
            raise rule_violation("no_resource", "resource")
        if willpower == 0 and resource is None:
            return
        if willpower:
            await self._spend_willpower(sheet, willpower)
        if resource is not None:
            await self._spend_resource(resource, cost)
        await self._access.changed(character.id)

    async def _spend_willpower(self, sheet: Sheet, amount: int) -> None:
        current = sheet.numbers["willpower_current"]
        if not await self._willpower.update_sheet_field(
            sheet.id, "willpower_current", current - amount, current
        ):
            raise _conflict("La volonté a changé.")

    async def _spend_resource(self, resource: Resource, amount: int) -> None:
        current = resource.current_value
        if not await self._resources.update_resource(
            resource.id, ResourceField.CURRENT, current - amount, current
        ):
            raise _conflict("La ressource a changé.")


def _resource_of(character: Character, recipe: RollRecipe | None) -> Resource | None:
    """Ressource dépensée par la recette ; ``None`` sans coût en ressource.

    Raises:
        AppError: ``rule_violation`` si la ressource n'est plus sur le personnage.
    """
    if recipe is None or recipe.resource_id is None or recipe.resource_cost == 0:
        return None
    resource = character.resource(recipe.resource_id)
    if resource is None:
        raise rule_violation("recipe_resource", "resource")
    return resource
