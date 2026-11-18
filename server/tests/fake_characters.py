"""Doublure de test : dépôt en mémoire des personnages et de leurs éléments.

Reproduit le comportement des dépôts PostgreSQL utile aux services : écriture
conditionnelle d'un champ, copie d'une forme, tactiques partagées.
"""

import copy
from dataclasses import asdict, replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.character import (
    Character,
    Entry,
    EntryKind,
    Expense,
    MoralityNote,
    Note,
    SeatCharacter,
    Sheet,
    Tactic,
)
from app.domain.npc_profile import NpcProfile
from app.domain.sheet_fields import NUMBER_FIELDS, TEXT_FIELDS
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES
from app.repositories.characters import NewCharacter
from app.repositories.sheet_items import EntryValues, ItemKind
from tests.fakes import FakeAccountStore


def _now() -> datetime:
    return datetime.now(UTC)


class FakeCharacterStore:
    """Personnages en mémoire. ``awaken`` simule le déclenchement de l'éveil par le MJ."""

    def __init__(self, accounts: FakeAccountStore) -> None:
        self._accounts = accounts
        self._characters: dict[UUID, Character] = {}
        self._played: dict[UUID, UUID] = {}
        self._tactics: dict[UUID, Tactic] = {}

    # --- Personnages --------------------------------------------------------------------

    def _put(self, character: Character) -> None:
        self._characters[character.id] = character

    def _edit_sheet(self, sheet_id: UUID, **changes: Any) -> None:
        for character in self._characters.values():
            if character.sheet(sheet_id) is not None:
                sheets = [
                    replace(s, **changes) if s.id == sheet_id else s for s in character.sheets
                ]
                self._put(replace(character, sheets=sheets))

    def _sheet(self, sheet_id: UUID) -> Sheet:
        return next(
            sheet for c in self._characters.values() for sheet in c.sheets if sheet.id == sheet_id
        )

    def awaken(self, character_id: UUID) -> None:
        self._put(replace(self._characters[character_id], awakened_at=_now()))

    async def mark_awakened(self, character_id: UUID) -> None:
        if self._characters[character_id].awakened_at is None:
            self.awaken(character_id)

    def owned_by(self, owner_id: UUID) -> list[Character]:
        """Personnages d'un compte, du plus ancien au plus récent."""
        return [c for c in self._characters.values() if c.owner_id == owner_id]

    async def get(self, character_id: UUID) -> Character | None:
        character = self._characters.get(character_id)
        if character is None:
            return None
        sheets = [
            replace(s, tactics=[self._tactics[t.id] for t in s.tactics]) for s in character.sheets
        ]
        owner = character.owner_id
        played = owner is not None and self._played.get(owner) == character.id
        return copy.deepcopy(replace(character, sheets=sheets, is_played=played))

    async def list_for_owner(self, owner_id: UUID) -> list[Character]:
        owned = [c.id for c in self._characters.values() if c.owner_id == owner_id]
        return [c for c in [await self.get(cid) for cid in owned] if c is not None]

    async def create(self, owner_id: UUID, new: NewCharacter) -> UUID:
        character = self._build(owner_id, new, npc=None)
        self._played[owner_id] = character.id
        return character.id

    def add_npc(self, new: NewCharacter, profile: NpcProfile) -> UUID:
        """Crée un PNJ sans propriétaire (doublure de ``PgNpcRepository.create_npc``)."""
        return self._build(None, new, npc=profile).id

    def set_npc(self, character_id: UUID, profile: NpcProfile) -> None:
        self._put(replace(self._characters[character_id], npc=profile))

    def characters(self) -> list[Character]:
        return list(self._characters.values())

    def put(self, character: Character) -> None:
        """Remplace un personnage, pour les doublures construites sur ce dépôt."""
        self._put(character)

    def npcs(self) -> list[Character]:
        return [c for c in self._characters.values() if c.npc is not None]

    def _build(self, owner_id: UUID | None, new: NewCharacter, npc: NpcProfile | None) -> Character:
        values = dict(new.values)
        specialties: dict[str, list[str]] = {}
        for specialty in new.specialties:
            specialties.setdefault(specialty.skill, []).append(specialty.label)
        sheet = Sheet(
            id=uuid4(),
            is_main=True,
            form_name=str(values["form_name"]),
            texts={f: str(values.get(f, "")) for f in TEXT_FIELDS if f != "form_name"},
            traits={
                n: int(values.get(n, 1 if n in ATTRIBUTE_NAMES else 0))
                for n in (*ATTRIBUTE_NAMES, *SKILL_NAMES)
            },
            numbers={f: int(values.get(f, 7)) for f in NUMBER_FIELDS},
            wound_track="",
            specialties=specialties,
            morality_notes=[],
            entries=[],
            tactics=[],
        )
        character = Character(
            id=uuid4(),
            owner_id=owner_id,
            owner_name="" if owner_id is None else self._accounts.accounts[owner_id].display_name,
            awakened_at=None,
            supernatural_level=1,
            supernatural_name="",
            xp_general_total=0,
            xp_tactical_total=0,
            is_played=False,
            sheets=[sheet],
            expenses=[],
            notes=[],
            npc=npc,
        )
        self._put(character)
        return character

    async def delete(self, character_id: UUID) -> None:
        character = self._characters.pop(character_id)
        owner = character.owner_id
        if owner is not None and self._played.get(owner) == character_id:
            del self._played[owner]

    async def set_played(self, owner_id: UUID, character_id: UUID) -> None:
        self._played[owner_id] = character_id

    async def update_character_field(
        self, character_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool:
        character = self._characters[character_id]
        if getattr(character, field) != expected:
            return False
        change: dict[str, Any] = {field: value}
        self._put(replace(character, **change))
        return True

    async def update_sheet_field(
        self, sheet_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool:
        sheet = self._sheet(sheet_id)
        if field in ("form_name", "wound_track"):
            if getattr(sheet, field) != expected:
                return False
            self._edit_sheet(sheet_id, **{field: value})
            return True
        group = (
            "texts" if field in TEXT_FIELDS else "numbers" if field in NUMBER_FIELDS else "traits"
        )
        values = dict(getattr(sheet, group))
        if values[field] != expected:
            return False
        values[field] = value
        self._edit_sheet(sheet_id, **{group: values})
        return True

    async def add_form(self, character_id: UUID, form_name: str) -> UUID:
        character = self._characters[character_id]
        main = character.main_sheet
        form = replace(
            copy.deepcopy(main),
            id=uuid4(),
            is_main=False,
            form_name=form_name,
            entries=[replace(e, id=uuid4()) for e in main.entries],
            morality_notes=[replace(n, id=uuid4()) for n in main.morality_notes],
        )
        self._put(replace(character, sheets=[*character.sheets, form]))
        return form.id

    async def delete_form(self, sheet_id: UUID) -> None:
        for character in list(self._characters.values()):
            kept = [s for s in character.sheets if s.id != sheet_id or s.is_main]
            self._put(replace(character, sheets=kept))

    async def played_by(self, account_ids: list[UUID]) -> dict[UUID, SeatCharacter]:
        seats: dict[UUID, SeatCharacter] = {}
        for account_id in account_ids:
            character = self._characters.get(self._played.get(account_id, uuid4()))
            if character is not None:
                main = character.main_sheet
                seats[account_id] = SeatCharacter(
                    character_id=character.id,
                    name=main.texts["name"],
                    concept=main.texts["concept"],
                    health_max=main.numbers["health_max"],
                    wound_track=main.wound_track,
                    willpower_max=main.numbers["willpower_max"],
                    willpower_current=main.numbers["willpower_current"],
                )
        return seats

    # --- Éléments -----------------------------------------------------------------------

    async def character_id_of(self, kind: ItemKind, item_id: UUID) -> UUID | None:
        for character in self._characters.values():
            ids: list[UUID] = {
                ItemKind.SHEET: [s.id for s in character.sheets],
                ItemKind.ENTRY: [e.id for s in character.sheets for e in s.entries],
                ItemKind.MORALITY_NOTE: [n.id for s in character.sheets for n in s.morality_notes],
                ItemKind.EXPENSE: [e.id for e in character.expenses],
                ItemKind.NOTE: [n.id for n in character.notes],
            }[kind]
            if item_id in ids:
                return character.id
        return None

    async def replace_specialties(self, sheet_id: UUID, skill: str, labels: list[str]) -> None:
        specialties = {k: v for k, v in self._sheet(sheet_id).specialties.items() if k != skill}
        if labels:
            specialties[skill] = list(labels)
        self._edit_sheet(sheet_id, specialties=specialties)

    async def add_morality_note(self, sheet_id: UUID, level: int, body: str) -> None:
        notes = [*self._sheet(sheet_id).morality_notes, MoralityNote(uuid4(), level, body)]
        self._edit_sheet(sheet_id, morality_notes=notes)

    def _sheet_holding(self, attribute: str, item_id: UUID) -> Sheet:
        return next(
            s
            for c in self._characters.values()
            for s in c.sheets
            if any(item.id == item_id for item in getattr(s, attribute))
        )

    async def update_morality_note(self, note_id: UUID, level: int, body: str) -> None:
        sheet = self._sheet_holding("morality_notes", note_id)
        notes = [
            MoralityNote(note_id, level, body) if n.id == note_id else n
            for n in sheet.morality_notes
        ]
        self._edit_sheet(sheet.id, morality_notes=notes)

    async def delete_morality_note(self, note_id: UUID) -> None:
        sheet = self._sheet_holding("morality_notes", note_id)
        self._edit_sheet(
            sheet.id, morality_notes=[n for n in sheet.morality_notes if n.id != note_id]
        )

    async def add_entry(self, sheet_id: UUID, kind: EntryKind, values: EntryValues) -> None:
        entry = Entry(id=uuid4(), kind=kind, **asdict(values))
        self._edit_sheet(sheet_id, entries=[*self._sheet(sheet_id).entries, entry])

    async def get_entry_kind(self, entry_id: UUID) -> EntryKind | None:
        sheet = self._sheet_holding("entries", entry_id)
        return next(e.kind for e in sheet.entries if e.id == entry_id)

    async def update_entry(self, entry_id: UUID, values: EntryValues) -> None:
        sheet = self._sheet_holding("entries", entry_id)
        entries = [
            Entry(id=e.id, kind=e.kind, **asdict(values)) if e.id == entry_id else e
            for e in sheet.entries
        ]
        self._edit_sheet(sheet.id, entries=entries)

    async def delete_entry(self, entry_id: UUID) -> None:
        sheet = self._sheet_holding("entries", entry_id)
        self._edit_sheet(sheet.id, entries=[e for e in sheet.entries if e.id != entry_id])

    async def list_tactics(self) -> list[Tactic]:
        return list(self._tactics.values())

    async def tactic_exists(self, tactic_id: UUID) -> bool:
        return tactic_id in self._tactics

    async def create_tactic(self, sheet_id: UUID, name: str, description: str) -> None:
        tactic = Tactic(uuid4(), name, description)
        self._tactics[tactic.id] = tactic
        await self.link_tactic(sheet_id, tactic.id)

    async def link_tactic(self, sheet_id: UUID, tactic_id: UUID) -> None:
        if not await self.is_tactic_linked(sheet_id, tactic_id):
            tactics = [*self._sheet(sheet_id).tactics, self._tactics[tactic_id]]
            self._edit_sheet(sheet_id, tactics=tactics)

    async def is_tactic_linked(self, sheet_id: UUID, tactic_id: UUID) -> bool:
        return any(t.id == tactic_id for t in self._sheet(sheet_id).tactics)

    def _knowing(self, tactic_id: UUID) -> list[UUID]:
        return [
            c.id
            for c in self._characters.values()
            if any(t.id == tactic_id for s in c.sheets for t in s.tactics)
        ]

    async def update_tactic(self, tactic_id: UUID, name: str, description: str) -> list[UUID]:
        self._tactics[tactic_id] = Tactic(tactic_id, name, description)
        return self._knowing(tactic_id)

    async def unlink_tactic(self, sheet_id: UUID, tactic_id: UUID) -> None:
        tactics = [t for t in self._sheet(sheet_id).tactics if t.id != tactic_id]
        self._edit_sheet(sheet_id, tactics=tactics)
        if not self._knowing(tactic_id):
            self._tactics.pop(tactic_id, None)

    async def add_expense(
        self, character_id: UUID, is_tactical: bool, points: int, justification: str
    ) -> None:
        character = self._characters[character_id]
        expense = Expense(uuid4(), is_tactical, points, justification, _now())
        self._put(replace(character, expenses=[expense, *character.expenses]))

    def _holding(self, attribute: str, item_id: UUID) -> Character:
        return next(
            c
            for c in self._characters.values()
            if any(item.id == item_id for item in getattr(c, attribute))
        )

    async def update_expense(self, expense_id: UUID, points: int, justification: str) -> None:
        character = self._holding("expenses", expense_id)
        expenses = [
            replace(e, points=points, justification=justification) if e.id == expense_id else e
            for e in character.expenses
        ]
        self._put(replace(character, expenses=expenses))

    async def delete_expense(self, expense_id: UUID) -> None:
        character = self._holding("expenses", expense_id)
        self._put(
            replace(character, expenses=[e for e in character.expenses if e.id != expense_id])
        )

    async def add_note(self, character_id: UUID, title: str, body: str) -> UUID:
        character = self._characters[character_id]
        note = Note(uuid4(), title, body, _now())
        self._put(replace(character, notes=[note, *character.notes]))
        return note.id

    async def update_note(self, note_id: UUID, title: str, body: str) -> None:
        character = self._holding("notes", note_id)
        notes = [
            Note(note_id, title, body, _now()) if n.id == note_id else n for n in character.notes
        ]
        self._put(replace(character, notes=notes))

    async def delete_note(self, note_id: UUID) -> None:
        character = self._holding("notes", note_id)
        self._put(replace(character, notes=[n for n in character.notes if n.id != note_id]))
