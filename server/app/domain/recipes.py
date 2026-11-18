"""Recette de jet d'un pouvoir, d'une arme ou d'un atout.

Le joueur, avec l'accord du MJ, choisit librement ce qui compose la réserve :
attributs, compétences, niveau de l'élément, bonus de l'arme. Il fixe aussi le
coût en Volonté et, s'il le veut, un coût dans une ressource libre du
personnage (Mana…) : les deux se cumulent et sont dépensés à chaque
utilisation. Un pouvoir ajoute toujours l'Avantage surnaturel du personnage
(son niveau au recto) : ce n'est pas un choix. Au moment du jet, seuls le malus et le bonus du MJ restent à saisir.

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.character import Entry, EntryKind
from app.domain.dice import UNSKILLED_PENALTY, DiceRuleError, PoolPart, skill_category
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES

SUPERNATURAL = "supernatural"
ENTRY_LEVEL = "entry_level"
WEAPON_BONUS = "weapon_bonus"
RECIPE_KEYS = frozenset({*ATTRIBUTE_NAMES, *SKILL_NAMES, ENTRY_LEVEL, WEAPON_BONUS})
# Éléments qui peuvent porter une recette.
ROLLABLE_KINDS = frozenset({EntryKind.POWER, EntryKind.WEAPON, EntryKind.MERIT})

PARTS_MAX = 8
COST_MAX = 5
BONUS_MIN = -10
BONUS_MAX = 10


@dataclass(frozen=True, slots=True)
class RollRecipe:
    """Composition de la réserve, coûts en Volonté et en ressource, bonus fixe.

    ``resource_id`` désigne la ressource libre dépensée ; il vaut ``None`` quand
    ``resource_cost`` est nul.
    """

    parts: tuple[str, ...]
    willpower_cost: int = 0
    bonus: int = 0
    resource_id: UUID | None = None
    resource_cost: int = 0

    def as_data(self) -> dict[str, Any]:
        """Forme enregistrée en base et renvoyée au client."""
        has_resource = self.resource_id is not None and self.resource_cost > 0
        return {
            "parts": list(self.parts),
            "willpower_cost": self.willpower_cost,
            "bonus": self.bonus,
            "resource_id": str(self.resource_id) if has_resource else None,
            "resource_cost": self.resource_cost if has_resource else 0,
        }

    @classmethod
    def from_data(cls, data: dict[str, Any] | None) -> "RollRecipe | None":
        """Relit une recette enregistrée ; ``None`` sans recette."""
        if not data:
            return None
        resource_id = data.get("resource_id")
        # L'Avantage surnaturel ne se choisit pas : il est ajouté à tout pouvoir.
        return cls(
            parts=tuple(str(part) for part in data.get("parts", []) if part != SUPERNATURAL),
            willpower_cost=int(data.get("willpower_cost", 0)),
            bonus=int(data.get("bonus", 0)),
            resource_id=UUID(str(resource_id)) if resource_id else None,
            resource_cost=int(data.get("resource_cost") or 0),
        )


def check_recipe(recipe: RollRecipe) -> None:
    """Refuse une recette vide, trop longue, inconnue ou hors bornes.

    Raises:
        DiceRuleError: pour une recette invalide.
    """
    if not 1 <= len(recipe.parts) <= PARTS_MAX:
        raise DiceRuleError("recipe_parts")
    if any(part not in RECIPE_KEYS for part in recipe.parts):
        raise DiceRuleError("recipe_parts")
    if not 0 <= recipe.willpower_cost <= COST_MAX:
        raise DiceRuleError("recipe_cost")
    if not 0 <= recipe.resource_cost <= COST_MAX:
        raise DiceRuleError("recipe_cost")
    if recipe.resource_cost > 0 and recipe.resource_id is None:
        raise DiceRuleError("recipe_resource")
    if not BONUS_MIN <= recipe.bonus <= BONUS_MAX:
        raise DiceRuleError("recipe_bonus")


def recipe_parts(
    recipe: RollRecipe, traits: dict[str, int], supernatural_level: int, entry: Entry
) -> list[PoolPart]:
    """Réserve d'un élément : chaque trait de la recette, l'Avantage surnaturel
    pour un pouvoir, puis le bonus fixe éventuel.

    Une compétence à 0 donne son malus de catégorie, comme pour tout jet.
    """
    parts: list[PoolPart] = []
    for key in recipe.parts:
        if key == ENTRY_LEVEL:
            parts.append(PoolPart(key, entry.level or 0))
        elif key == WEAPON_BONUS:
            parts.append(PoolPart(key, entry.damage_modifier or 0))
        else:
            parts.append(PoolPart(key, traits[key]))
            if key in SKILL_NAMES and traits[key] == 0:
                parts.append(PoolPart("unskilled", UNSKILLED_PENALTY[skill_category(key)]))
    if entry.kind is EntryKind.POWER:
        parts.append(PoolPart(SUPERNATURAL, supernatural_level))
    if recipe.bonus:
        parts.append(PoolPart("bonus", recipe.bonus))
    return parts
