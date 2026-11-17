"""Cas d'usage des personnages : création, consultation, modification, suppression.

Le joueur gère ses personnages ; le MJ consulte et modifie ceux de tous les
joueurs. Gère aussi les formes du personnage et le personnage joué à la table.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.accounts import Account, Role
from app.domain.character import Character
from app.domain.creation import (
    Priorities,
    Specialty,
    attribute_violations,
    skill_violations,
    specialty_violations,
)
from app.domain.derived import BASE_SIZE, base_values
from app.domain.npcs import check_npc_sheet_field
from app.domain.sheet_fields import (
    NUMBER_FIELDS,
    TEXT_FIELDS,
    FieldRule,
    FieldRuleError,
    current_value,
    validate_field,
)
from app.domain.wounds import Wound, WoundRuleError, add_wound, heal_wound, worsen_wound
from app.repositories.characters import CHARACTER_FIELDS, NewCharacter
from app.repositories.sheet_items import ItemKind
from app.services.character_access import (
    CharacterAccess,
    edit_conflict,
    not_found,
    require_player_character,
    rule_violation,
)

MAIN_FORM_NAME = "Forme principale"
_IDENTITY_FIELDS = ("name", "concept", "profession", "virtue", "vice", "compact")
_EFFECTIVE_FIELDS = ("size", "speed", "defense", "initiative", "health_max", "willpower_max")
_CHARACTER_NUMBER_RANGES = {
    "supernatural_level": (1, 10),
    "xp_general_total": (0, 99999),
    "xp_tactical_total": (0, 99999),
}
_SUPERNATURAL_NAME_MAX = 60


@dataclass(frozen=True, slots=True)
class CreationInput:
    """Saisie complète de l'assistant de création.

    Attributs:
        identity: nom (obligatoire), concept, profession, vertu, vice, compact.
        effective: valeurs effectives retenues à l'étape 5 ; une valeur absente
            reprend la valeur de base calculée.
    """

    identity: Mapping[str, str]
    attribute_priorities: Priorities
    attributes: Mapping[str, int]
    skill_priorities: Priorities
    skills: Mapping[str, int]
    specialties: Sequence[Specialty]
    effective: Mapping[str, int]


class CharacterStore(Protocol):
    """Contrat d'accès aux personnages attendu par le service."""

    async def get(self, character_id: UUID) -> Character | None: ...

    async def list_for_owner(self, owner_id: UUID) -> list[Character]: ...

    async def create(self, owner_id: UUID, new: NewCharacter) -> UUID: ...

    async def delete(self, character_id: UUID) -> None: ...

    async def set_played(self, owner_id: UUID, character_id: UUID) -> None: ...

    async def update_character_field(
        self, character_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool: ...

    async def update_sheet_field(
        self, sheet_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool: ...

    async def add_form(self, character_id: UUID, form_name: str) -> UUID: ...

    async def delete_form(self, sheet_id: UUID) -> None: ...


class ItemLocator(Protocol):
    """Retrouve le personnage auquel se rattache une forme ou un élément."""

    async def character_id_of(self, kind: ItemKind, item_id: UUID) -> UUID | None: ...


class CharacterService:
    """Orchestre les personnages et leurs formes.

    Args:
        characters: dépôt des personnages.
        locator: retrouve le personnage auquel appartient une forme.
        access: droits, relecture et diffusion.
    """

    def __init__(
        self, characters: CharacterStore, locator: ItemLocator, access: CharacterAccess
    ) -> None:
        self._characters = characters
        self._locator = locator
        self._access = access

    async def list_for(self, actor: Account, owner_id: UUID) -> list[Character]:
        """Liste les personnages d'un compte : le sien, ou n'importe lequel pour le MJ.

        Raises:
            AppError: ``forbidden`` si un joueur demande ceux d'un autre.
        """
        if actor.role is not Role.GM and actor.id != owner_id:
            raise AppError(ErrorCode.FORBIDDEN, "Accès refusé.", status_code=403)
        return await self._characters.list_for_owner(owner_id)

    async def get(self, actor: Account, character_id: UUID) -> Character:
        """Retourne un personnage consultable par ``actor``."""
        return await self._access.readable(actor, character_id)

    async def create(self, actor: Account, creation: CreationInput) -> Character:
        """Crée un personnage à partir de l'assistant.

         L'état initial suit l'étape 5 : piste de blessures vide,
         volonté disponible égale à la volonté maximale, moralité à 7
        , expérience à zéro.

         Raises:
             AppError: ``forbidden`` pour le MJ, qui n'a pas de personnage ;
                 ``rule_violation`` si la répartition des points ou les
                 spécialités sont incorrectes, ou si une valeur est hors bornes.
        """
        if actor.role is not Role.PLAYER:
            raise AppError(
                ErrorCode.FORBIDDEN, "Seul un joueur crée un personnage.", status_code=403
            )
        violations = [
            *attribute_violations(creation.attribute_priorities, creation.attributes),
            *skill_violations(creation.skill_priorities, creation.skills),
            *specialty_violations(list(creation.specialties), creation.skills),
        ]
        if violations:
            raise AppError(
                ErrorCode.RULE_VIOLATION,
                "La feuille ne respecte pas les règles de création.",
                status_code=422,
                details=[
                    {"rule": v.rule.value} | ({"field": v.subject} if v.subject else {})
                    for v in violations
                ],
            )
        values = self._initial_values(creation)
        specialties = [Specialty(s.skill, s.label.strip()) for s in creation.specialties]
        character_id = await self._characters.create(actor.id, NewCharacter(values, specialties))
        return await self._access.changed(character_id)

    @staticmethod
    def _initial_values(creation: CreationInput) -> dict[str, str | int]:
        """Assemble les colonnes de la forme principale et contrôle leurs bornes."""
        traits = {**creation.attributes, **creation.skills}
        size = creation.effective.get("size", BASE_SIZE)
        base = base_values(traits, size)
        defaults = {
            "size": size,
            "speed": base.speed,
            "defense": base.defense,
            "initiative": base.initiative,
            "health_max": base.health,
            "willpower_max": base.willpower,
        }
        values: dict[str, str | int] = {"form_name": MAIN_FORM_NAME, **traits}
        for field in _IDENTITY_FIELDS:
            text = creation.identity.get(field, "").strip()
            if len(text) > TEXT_FIELDS[field]:
                raise rule_violation(FieldRule.LENGTH.value, field)
            values[field] = text
        if not values["name"]:
            raise rule_violation(FieldRule.REQUIRED.value, "name")
        for field in _EFFECTIVE_FIELDS:
            number = creation.effective.get(field, defaults[field])
            low, high = NUMBER_FIELDS[field]
            if not low <= number <= high:
                raise rule_violation(FieldRule.RANGE.value, field)
            values[field] = number
        values["willpower_current"] = values["willpower_max"]
        return values

    async def delete(self, actor: Account, character_id: UUID) -> None:
        """Supprime définitivement un personnage. Réservé à son propriétaire."""
        character = await self._access.readable(actor, character_id)
        if character.owner_id != actor.id:
            raise AppError(
                ErrorCode.FORBIDDEN,
                "Seul son propriétaire supprime un personnage.",
                status_code=403,
            )
        await self._characters.delete(character_id)
        await self._access.notify(character_id, character.owner_id, character.is_played)

    async def play(self, actor: Account, character_id: UUID) -> Character:
        """Désigne le personnage joué à la table. Réservé à son propriétaire."""
        character = await self._access.readable(actor, character_id)
        if character.owner_id != actor.id:
            raise AppError(
                ErrorCode.FORBIDDEN, "Seul son propriétaire joue un personnage.", status_code=403
            )
        await self._characters.set_played(actor.id, character_id)
        await self._access.notify(character_id, character.owner_id, seat_affected=True)
        return await self._access.readable(actor, character_id)

    async def set_character_field(
        self, actor: Account, character_id: UUID, field: str, value: object, expected: object
    ) -> Character:
        """Modifie un champ commun à toutes les formes : avantage surnaturel ou total d'expérience.

        Un total d'expérience ne descend pas sous les points déjà dépensés
        (le solde ne devient jamais négatif).

        Raises:
            AppError: ``rule_violation`` ou ``edit_conflict``.
        """
        character = await self._access.editable(actor, character_id)
        if field not in CHARACTER_FIELDS:
            raise rule_violation(FieldRule.UNKNOWN_FIELD.value, field)
        if field.startswith("xp_"):
            require_player_character(character, field)
        if field == "supernatural_name":
            if not isinstance(value, str) or not isinstance(expected, str):
                raise rule_violation(FieldRule.TYPE.value, field)
            checked: str | int = value.strip()
            if len(value.strip()) > _SUPERNATURAL_NAME_MAX:
                raise rule_violation(FieldRule.LENGTH.value, field)
        else:
            if isinstance(value, bool) or not isinstance(value, int):
                raise rule_violation(FieldRule.TYPE.value, field)
            low, high = _CHARACTER_NUMBER_RANGES[field]
            if not low <= value <= high:
                raise rule_violation(FieldRule.RANGE.value, field)
            if field != "supernatural_level" and value < character.xp_spent(
                tactical=field == "xp_tactical_total"
            ):
                raise rule_violation("xp_total_below_spent", field)
            checked = value
        if not isinstance(expected, str | int) or isinstance(expected, bool):
            raise rule_violation(FieldRule.TYPE.value, field)
        if not await self._characters.update_character_field(
            character_id, field, checked, expected
        ):
            raise edit_conflict()
        return await self._access.changed(character_id)

    async def set_sheet_field(
        self, actor: Account, sheet_id: UUID, field: str, value: object, expected: object
    ) -> Character:
        """Modifie un champ d'une forme, enregistré seul et aussitôt.

        Args:
            expected: valeur que l'acteur avait sous les yeux. Si elle n'est
                plus celle de la base, rien n'est écrit.

        Raises:
            AppError: ``rule_violation`` ou ``edit_conflict``.
        """
        character = await self._for_sheet(actor, sheet_id)
        sheet = self._access.sheet_of(character, sheet_id)
        try:
            check_npc_sheet_field(character.npc, field)
            # Un PNJ a des points libres : attributs jusqu'à 10.
            uncapped = character.is_awakened or character.is_npc
            checked = validate_field(sheet, field, value, uncapped)
            if type(expected) is not type(current_value(sheet, field)):
                raise FieldRuleError(FieldRule.TYPE)
        except FieldRuleError as error:
            raise rule_violation(error.rule.value, field) from None
        assert isinstance(expected, str | int)  # noqa: S101 - garanti par le contrôle de type
        if not await self._characters.update_sheet_field(sheet_id, field, checked, expected):
            raise edit_conflict()
        return await self._access.changed(character.id)

    async def change_wounds(
        self, actor: Account, sheet_id: UUID, action: str, wound: Wound | None, expected: str
    ) -> Character:
        """Ajoute, soigne ou aggrave une blessure.

        La piste reste rangée et sans trou et ne dépasse jamais la
        santé maximale.

        Args:
            action: ``add``, ``heal`` ou ``worsen``.
            wound: type de blessure ; facultatif pour ``heal``, qui retire
                alors la moins grave.
            expected: piste que l'acteur avait sous les yeux.

        Raises:
            AppError: ``rule_violation`` ou ``edit_conflict``.
        """
        character = await self._for_sheet(actor, sheet_id)
        sheet = self._access.sheet_of(character, sheet_id)
        if sheet.wound_track != expected:
            raise edit_conflict()
        try:
            if action == "heal":
                track = heal_wound(sheet.wound_track, wound)
            elif wound is None:
                raise WoundRuleError
            elif action == "add":
                track = add_wound(sheet.wound_track, wound, sheet.numbers["health_max"])
            else:
                track = worsen_wound(sheet.wound_track, wound)
        except WoundRuleError as error:
            raise rule_violation(type(error).__name__, "wound_track") from None
        if not await self._characters.update_sheet_field(sheet_id, "wound_track", track, expected):
            raise edit_conflict()
        return await self._access.changed(character.id)

    async def add_form(self, actor: Account, character_id: UUID, form_name: str) -> Character:
        """Ajoute une forme, copie de la forme principale. Jamais pour un PNJ."""
        require_player_character(await self._access.editable(actor, character_id), "form")
        await self._characters.add_form(character_id, form_name)
        return await self._access.changed(character_id)

    async def delete_form(self, actor: Account, sheet_id: UUID) -> Character:
        """Supprime une forme alternative.

        Raises:
            AppError: ``rule_violation`` pour la forme principale, jamais supprimable.
        """
        character = await self._for_sheet(actor, sheet_id)
        if self._access.sheet_of(character, sheet_id).is_main:
            raise rule_violation("main_form", "form")
        await self._characters.delete_form(sheet_id)
        return await self._access.changed(character.id)

    async def _for_sheet(self, actor: Account, sheet_id: UUID) -> Character:
        """Retourne le personnage modifiable auquel appartient la forme."""
        character_id = await self._locator.character_id_of(ItemKind.SHEET, sheet_id)
        if character_id is None:
            raise not_found()
        return await self._access.editable(actor, character_id)
