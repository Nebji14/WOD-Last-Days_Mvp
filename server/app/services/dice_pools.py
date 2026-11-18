"""Composition de la réserve d'un jet tiré d'une feuille.

Attribut et compétence choisis sur la fiche, recette d'un pouvoir, d'une arme
ou d'un atout, initiative, jet pour rester conscient, traits d'un PNJ
simplifié : le malus de blessure et le malus ou bonus du MJ s'y ajoutent.
"""

from dataclasses import dataclass
from uuid import UUID

from app.domain.character import Character, Entry, Sheet
from app.domain.dice import (
    NPC_TRAITS,
    DiceRuleError,
    PoolOptions,
    PoolPart,
    RollKind,
    bonus_parts,
    pool_parts,
)
from app.domain.recipes import RollRecipe, recipe_parts
from app.domain.wounds import wound_penalty


@dataclass(frozen=True, slots=True)
class RollInput:
    """Demande de jet validée, transmise par la route."""

    kind: RollKind
    options: PoolOptions
    character_id: UUID | None = None
    sheet_id: UUID | None = None
    attribute: str | None = None
    second: str | None = None
    trait: str | None = None
    dice: int | None = None
    entry_id: UUID | None = None
    secret: bool = False


def entry_of(sheet: Sheet, request: RollInput) -> Entry | None:
    """Pouvoir, arme ou atout lancé ; ``None`` pour un autre jet.

    Raises:
        DiceRuleError: si l'élément n'est pas sur cette forme.
    """
    if request.kind is not RollKind.ENTRY:
        return None
    entry = next((e for e in sheet.entries if e.id == request.entry_id), None)
    if entry is None:
        raise DiceRuleError("entry")
    return entry


def compose_pool(
    character: Character, sheet: Sheet, request: RollInput, entry: Entry | None
) -> tuple[list[PoolPart], int]:
    """Réserve du jet et, pour l'initiative, la valeur ajoutée au dé."""
    options = request.options
    penalty = wound_penalty(sheet.wound_track, sheet.numbers["health_max"])
    if entry is not None:
        recipe = RollRecipe.from_data(entry.roll)
        if recipe is None:
            raise DiceRuleError("recipe")
        parts = recipe_parts(recipe, sheet.traits, character.supernatural_level, entry)
        return [*parts, *bonus_parts(options, penalty)], 0
    reflex = request.kind in (RollKind.INITIATIVE, RollKind.CONSCIOUSNESS)
    if reflex and (options.willpower or options.specialty):
        raise DiceRuleError("options")
    if request.kind is RollKind.INITIATIVE:
        base = sheet.numbers["initiative"]
        return [PoolPart("initiative", base), *bonus_parts(PoolOptions(), penalty)], base
    if request.kind is RollKind.CONSCIOUSNESS:
        # Le malus de blessure ne s'applique pas à ce jet.
        stamina = PoolPart("stamina", sheet.traits["stamina"])
        adjust = PoolOptions(modifier=options.modifier, gm_bonus=options.gm_bonus)
        return [stamina, *bonus_parts(adjust, 0)], 0
    if request.kind is RollKind.TRAIT:
        profile = character.npc
        if profile is None or not profile.is_simplified or request.trait not in NPC_TRAITS:
            raise DiceRuleError("trait")
        value = getattr(profile, request.trait) or 0
        return [PoolPart(request.trait, value), *bonus_parts(options, penalty)], 0
    if character.npc is not None and character.npc.is_simplified:
        raise DiceRuleError("trait")
    attribute = request.attribute or ""
    return pool_parts(sheet.traits, attribute, request.second, options, penalty), 0
