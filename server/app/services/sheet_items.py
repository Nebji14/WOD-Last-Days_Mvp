"""Cas d'usage des éléments d'une fiche.

Spécialités, annotations de moralité, atouts, handicaps,
pouvoirs, objets, armes et armures, tactiques partagées,
dépenses d'expérience et notes de la fiche.
"""

from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.accounts import Account
from app.domain.character import Character, EntryKind, Tactic, can_manage_notes
from app.domain.dice import DiceRuleError
from app.domain.recipes import ROLLABLE_KINDS, RollRecipe, check_recipe
from app.domain.traits import SKILL_NAMES, SPECIALTY_MAX_LENGTH, parse_specialties
from app.repositories.sheet_items import EntryValues, ItemKind
from app.services.character_access import (
    CharacterAccess,
    not_found,
    require_player_character,
    rule_violation,
)

DEFAULT_NOTE_TITLE = "Sans titre"
_LEVELLED_KINDS = frozenset({EntryKind.MERIT, EntryKind.FLAW, EntryKind.POWER})


class SheetItemStore(Protocol):
    """Contrat d'accès aux éléments de feuille attendu par le service."""

    async def character_id_of(self, kind: ItemKind, item_id: UUID) -> UUID | None: ...

    async def replace_specialties(self, sheet_id: UUID, skill: str, labels: list[str]) -> None: ...

    async def add_morality_note(self, sheet_id: UUID, level: int, body: str) -> None: ...

    async def update_morality_note(self, note_id: UUID, level: int, body: str) -> None: ...

    async def delete_morality_note(self, note_id: UUID) -> None: ...

    async def add_entry(self, sheet_id: UUID, kind: EntryKind, values: EntryValues) -> None: ...

    async def get_entry_kind(self, entry_id: UUID) -> EntryKind | None: ...

    async def update_entry(self, entry_id: UUID, values: EntryValues) -> None: ...

    async def delete_entry(self, entry_id: UUID) -> None: ...

    async def list_tactics(self) -> list[Tactic]: ...

    async def tactic_exists(self, tactic_id: UUID) -> bool: ...

    async def create_tactic(self, sheet_id: UUID, name: str, description: str) -> None: ...

    async def link_tactic(self, sheet_id: UUID, tactic_id: UUID) -> None: ...

    async def is_tactic_linked(self, sheet_id: UUID, tactic_id: UUID) -> bool: ...

    async def update_tactic(self, tactic_id: UUID, name: str, description: str) -> list[UUID]: ...

    async def unlink_tactic(self, sheet_id: UUID, tactic_id: UUID) -> None: ...

    async def add_expense(
        self, character_id: UUID, is_tactical: bool, points: int, justification: str
    ) -> None: ...

    async def update_expense(self, expense_id: UUID, points: int, justification: str) -> None: ...

    async def delete_expense(self, expense_id: UUID) -> None: ...

    async def add_note(self, character_id: UUID, title: str, body: str) -> UUID: ...

    async def update_note(self, note_id: UUID, title: str, body: str) -> None: ...

    async def delete_note(self, note_id: UUID) -> None: ...


def normalize_entry(kind: EntryKind, values: EntryValues) -> EntryValues:
    """Ne garde que les champs propres au type de l'élément.

    Un atout a toujours un niveau (1 par défaut) ; le niveau d'un handicap ou
    d'un pouvoir est facultatif. Les autres champs ne valent que pour un objet
    (quantité), une arme ou une armure.
    """
    is_weapon = kind is EntryKind.WEAPON
    is_armor = kind is EntryKind.ARMOR
    level = values.level if kind in _LEVELLED_KINDS else None
    return EntryValues(
        name=values.name.strip(),
        description=values.description.strip(),
        level=1 if kind is EntryKind.MERIT and level is None else level,
        quantity=values.quantity if kind is EntryKind.ITEM else None,
        damage_modifier=values.damage_modifier if is_weapon else None,
        range=(values.range or "").strip() if is_weapon else None,
        size=values.size if is_weapon else None,
        initiative_penalty=values.initiative_penalty if is_weapon else None,
        general_protection=values.general_protection if is_armor else None,
        ballistic_protection=values.ballistic_protection if is_armor else None,
        min_strength=values.min_strength if is_armor else None,
        defense_penalty=values.defense_penalty if is_armor else None,
        roll=values.roll if kind in ROLLABLE_KINDS else None,
    )


def check_entry_roll(values: EntryValues) -> None:
    """Refuse une recette de jet invalide.

    Raises:
        AppError: ``rule_violation`` avec la règle enfreinte.
    """
    recipe = RollRecipe.from_data(values.roll)
    if recipe is None:
        return
    try:
        check_recipe(recipe)
    except DiceRuleError as error:
        raise rule_violation(str(error), "roll") from None


class SheetItemService:
    """Orchestre les éléments rattachés à une feuille ou à un personnage.

    Args:
        items: dépôt des éléments.
        access: droits, relecture et diffusion.
    """

    def __init__(self, items: SheetItemStore, access: CharacterAccess) -> None:
        self._items = items
        self._access = access

    async def _owner_of(self, actor: Account, kind: ItemKind, item_id: UUID) -> Character:
        """Retourne le personnage modifiable auquel se rattache l'élément."""
        return await self._access.editable(actor, await self._items.character_id_of(kind, item_id))

    async def _sheet_owner(self, actor: Account, sheet_id: UUID) -> Character:
        return await self._owner_of(actor, ItemKind.SHEET, sheet_id)

    # --- Spécialités ------------------------------------------------------------

    async def set_specialties(
        self, actor: Account, sheet_id: UUID, skill: str, text: str
    ) -> Character:
        """Remplace les spécialités d'une compétence à partir du champ saisi.

        Les spécialités sont séparées par des virgules ; un champ vide les
        supprime toutes.

        Raises:
            AppError: ``rule_violation`` si la compétence est inconnue.
        """
        character = await self._sheet_owner(actor, sheet_id)
        if skill not in SKILL_NAMES or (character.npc is not None and character.npc.is_simplified):
            raise rule_violation("unknown_field", skill)
        labels = [label[:SPECIALTY_MAX_LENGTH] for label in parse_specialties(text)]
        await self._items.replace_specialties(sheet_id, skill, labels)
        return await self._access.changed(character.id)

    # --- Annotations de moralité ----------------------------------------

    async def add_morality_note(
        self, actor: Account, sheet_id: UUID, level: int, body: str
    ) -> Character:
        character = await self._sheet_owner(actor, sheet_id)
        await self._items.add_morality_note(sheet_id, level, body)
        return await self._access.changed(character.id)

    async def update_morality_note(
        self, actor: Account, note_id: UUID, level: int, body: str
    ) -> Character:
        character = await self._owner_of(actor, ItemKind.MORALITY_NOTE, note_id)
        await self._items.update_morality_note(note_id, level, body)
        return await self._access.changed(character.id)

    async def delete_morality_note(self, actor: Account, note_id: UUID) -> Character:
        character = await self._owner_of(actor, ItemKind.MORALITY_NOTE, note_id)
        await self._items.delete_morality_note(note_id)
        return await self._access.changed(character.id)

    # --- Atouts, handicaps, pouvoirs, objets, armes, armures --------------------

    async def add_entry(
        self, actor: Account, sheet_id: UUID, kind: EntryKind, values: EntryValues
    ) -> Character:
        character = await self._sheet_owner(actor, sheet_id)
        normalized = normalize_entry(kind, values)
        check_entry_roll(normalized)
        await self._items.add_entry(sheet_id, kind, normalized)
        return await self._access.changed(character.id)

    async def update_entry(self, actor: Account, entry_id: UUID, values: EntryValues) -> Character:
        character = await self._owner_of(actor, ItemKind.ENTRY, entry_id)
        kind = await self._items.get_entry_kind(entry_id)
        if kind is None:
            raise not_found()
        normalized = normalize_entry(kind, values)
        check_entry_roll(normalized)
        await self._items.update_entry(entry_id, normalized)
        return await self._access.changed(character.id)

    async def delete_entry(self, actor: Account, entry_id: UUID) -> Character:
        character = await self._owner_of(actor, ItemKind.ENTRY, entry_id)
        await self._items.delete_entry(entry_id)
        return await self._access.changed(character.id)

    # --- Tactiques partagées -----------------------------------------------

    async def list_tactics(self) -> list[Tactic]:
        """Liste les tactiques existantes, pour en rattacher une à une feuille."""
        return await self._items.list_tactics()

    async def add_tactic(
        self, actor: Account, sheet_id: UUID, name: str, description: str
    ) -> Character:
        """Crée une tactique et la rattache à la feuille. Pas de tactique pour un PNJ."""
        character = await self._sheet_owner(actor, sheet_id)
        require_player_character(character, "tactic")
        await self._items.create_tactic(sheet_id, name.strip(), description.strip())
        return await self._access.changed(character.id)

    async def link_tactic(self, actor: Account, sheet_id: UUID, tactic_id: UUID) -> Character:
        """Rattache à la feuille une tactique déjà connue d'un autre personnage."""
        character = await self._sheet_owner(actor, sheet_id)
        require_player_character(character, "tactic")
        if not await self._items.tactic_exists(tactic_id):
            raise not_found()
        await self._items.link_tactic(sheet_id, tactic_id)
        return await self._access.changed(character.id)

    async def update_tactic(
        self, actor: Account, sheet_id: UUID, tactic_id: UUID, name: str, description: str
    ) -> Character:
        """Modifie une tactique depuis une feuille qui la connaît.

        La tactique est partagée : le changement vaut pour toutes les feuilles
        qui la connaissent, et leurs lecteurs sont prévenus.
        """
        character = await self._sheet_owner(actor, sheet_id)
        if not await self._items.is_tactic_linked(sheet_id, tactic_id):
            raise not_found()
        others = await self._items.update_tactic(tactic_id, name.strip(), description.strip())
        for character_id in others:
            if character_id != character.id:
                await self._access.changed(character_id)
        return await self._access.changed(character.id)

    async def remove_tactic(self, actor: Account, sheet_id: UUID, tactic_id: UUID) -> Character:
        """Détache une tactique de la feuille."""
        character = await self._sheet_owner(actor, sheet_id)
        await self._items.unlink_tactic(sheet_id, tactic_id)
        return await self._access.changed(character.id)

    # --- Dépenses d'expérience ---------------------------------

    async def add_expense(
        self, actor: Account, character_id: UUID, is_tactical: bool, points: int, justification: str
    ) -> Character:
        """Enregistre une dépense : le solde baisse, le total acquis ne change pas.

        Raises:
            AppError: ``rule_violation`` si le solde est insuffisant.
        """
        character = await self._access.editable(actor, character_id)
        require_player_character(character, "points")
        if points > character.xp_balance(is_tactical):
            raise rule_violation("xp_insufficient", "points")
        await self._items.add_expense(character_id, is_tactical, points, justification.strip())
        return await self._access.changed(character_id)

    async def update_expense(
        self, actor: Account, expense_id: UUID, points: int, justification: str
    ) -> Character:
        """Corrige une dépense ; le solde ne peut pas devenir négatif."""
        character = await self._owner_of(actor, ItemKind.EXPENSE, expense_id)
        expense = next((e for e in character.expenses if e.id == expense_id), None)
        if expense is None:
            raise not_found()
        if points - expense.points > character.xp_balance(expense.is_tactical):
            raise rule_violation("xp_insufficient", "points")
        await self._items.update_expense(expense_id, points, justification.strip())
        return await self._access.changed(character.id)

    async def delete_expense(self, actor: Account, expense_id: UUID) -> Character:
        character = await self._owner_of(actor, ItemKind.EXPENSE, expense_id)
        await self._items.delete_expense(expense_id)
        return await self._access.changed(character.id)

    # --- Notes de la fiche --------------------------------------------------------------

    async def add_note(self, actor: Account, character_id: UUID) -> tuple[Character, UUID]:
        """Crée une note vide « Sans titre ».

        Returns:
            Le personnage à jour et l'identifiant de la note créée.
        """
        character = await self._access.readable(actor, character_id)
        self._require_note_owner(actor, character)
        note_id = await self._items.add_note(character_id, DEFAULT_NOTE_TITLE, "")
        return await self._access.changed(character_id), note_id

    async def update_note(self, actor: Account, note_id: UUID, title: str, body: str) -> Character:
        character = await self._note_owner(actor, note_id)
        await self._items.update_note(note_id, title.strip(), body)
        return await self._access.changed(character.id)

    async def delete_note(self, actor: Account, note_id: UUID) -> Character:
        character = await self._note_owner(actor, note_id)
        await self._items.delete_note(note_id)
        return await self._access.changed(character.id)

    async def _note_owner(self, actor: Account, note_id: UUID) -> Character:
        character_id = await self._items.character_id_of(ItemKind.NOTE, note_id)
        if character_id is None:
            raise not_found()
        character = await self._access.readable(actor, character_id)
        self._require_note_owner(actor, character)
        return character

    @staticmethod
    def _require_note_owner(actor: Account, character: Character) -> None:
        """Le MJ lit les notes d'un joueur mais ne les modifie pas."""
        if not can_manage_notes(actor, character.owner_id):
            raise AppError(
                ErrorCode.FORBIDDEN,
                "Seul le propriétaire gère les notes de sa fiche.",
                status_code=403,
            )
