"""Modèles de sortie des personnages.

Secret de l'éveil : tant qu'il n'est pas déclenché, la
réponse faite à un joueur ne contient aucun champ qui s'y rapporte. Trois
modèles portent cette règle : ``CharacterResponse`` (joueur, non éveillé),
``AwakenedCharacterResponse`` (joueur, éveillé) et ``GmCharacterResponse`` (MJ).
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel

from app.domain.accounts import Account, Role
from app.domain.character import Character, EntryKind, Sheet, can_manage_notes
from app.domain.derived import base_values
from app.domain.npc_profile import NpcModel, NpcProfile
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES
from app.schemas.resources import ResourceResponse

_EFFECTIVE_FIELDS = ("size", "speed", "defense", "initiative", "health_max", "willpower_max")


class EntryResponse(BaseModel):
    """Élément de feuille ; les champs étrangers à son type valent ``null``."""

    id: UUID
    kind: EntryKind
    name: str
    description: str
    level: int | None
    quantity: int | None
    damage_modifier: int | None
    range: str | None
    size: int | None
    initiative_penalty: int | None
    general_protection: int | None
    ballistic_protection: int | None
    min_strength: int | None
    defense_penalty: int | None
    roll: dict[str, Any] | None = None


class MoralityNoteResponse(BaseModel):
    id: UUID
    level: int
    body: str


class TacticResponse(BaseModel):
    id: UUID
    name: str
    description: str


class ExpenseResponse(BaseModel):
    id: UUID
    is_tactical: bool
    points: int
    justification: str
    created_at: datetime


class NoteResponse(BaseModel):
    id: UUID
    title: str
    body: str
    updated_at: datetime


class SheetResponse(BaseModel):
    """Forme d'un personnage.

    Attributs:
        effective: valeurs saisies et stockées.
        base: valeurs de référence, recalculées à chaque lecture, jamais
            stockées.
    """

    id: UUID
    is_main: bool
    form_name: str
    texts: dict[str, str]
    attributes: dict[str, int]
    skills: dict[str, int]
    effective: dict[str, int]
    base: dict[str, int]
    wound_track: str
    willpower_current: int
    morality: int
    specialties: dict[str, list[str]]
    morality_notes: list[MoralityNoteResponse]
    entries: list[EntryResponse]
    tactics: list[TacticResponse]
    portrait: str | None

    @classmethod
    def from_sheet(cls, sheet: Sheet) -> "SheetResponse":
        """Projette une forme et calcule ses valeurs de base."""
        base = base_values(sheet.traits, sheet.numbers["size"])
        return cls(
            id=sheet.id,
            is_main=sheet.is_main,
            form_name=sheet.form_name,
            texts=sheet.texts,
            attributes={name: sheet.traits[name] for name in ATTRIBUTE_NAMES},
            skills={name: sheet.traits[name] for name in SKILL_NAMES},
            effective={field: sheet.numbers[field] for field in _EFFECTIVE_FIELDS},
            base={
                "size": base.size,
                "speed": base.speed,
                "defense": base.defense,
                "initiative": base.initiative,
                "health_max": base.health,
                "willpower_max": base.willpower,
            },
            wound_track=sheet.wound_track,
            willpower_current=sheet.numbers["willpower_current"],
            morality=sheet.numbers["morality"],
            specialties=sheet.specialties,
            morality_notes=[
                MoralityNoteResponse(id=n.id, level=n.level, body=n.body)
                for n in sheet.morality_notes
            ],
            entries=[
                EntryResponse(
                    id=e.id,
                    kind=e.kind,
                    name=e.name,
                    description=e.description,
                    level=e.level,
                    quantity=e.quantity,
                    damage_modifier=e.damage_modifier,
                    range=e.range,
                    size=e.size,
                    initiative_penalty=e.initiative_penalty,
                    general_protection=e.general_protection,
                    ballistic_protection=e.ballistic_protection,
                    min_strength=e.min_strength,
                    defense_penalty=e.defense_penalty,
                    roll=e.roll,
                )
                for e in sheet.entries
            ],
            tactics=[
                TacticResponse(id=t.id, name=t.name, description=t.description)
                for t in sheet.tactics
            ],
            portrait=sheet.portrait,
        )


class ExperienceResponse(BaseModel):
    """Total acquis et solde d'un type d'expérience, toujours distincts."""

    total: int
    balance: int


class NpcProfileResponse(BaseModel):
    """Données propres à une feuille de PNJ, lues par le MJ seul."""

    model: NpcModel
    category_id: UUID | None
    notes: str
    power: int | None
    finesse: int | None
    resilience: int | None

    @classmethod
    def from_profile(cls, profile: NpcProfile) -> "NpcProfileResponse":
        return cls(
            model=profile.model,
            category_id=profile.category_id,
            notes=profile.notes,
            power=profile.power,
            finesse=profile.finesse,
            resilience=profile.resilience,
        )


class CharacterResponse(BaseModel):
    """Personnage tel qu'il est exposé à un joueur dont le personnage n'est pas éveillé.

    ``owner_id`` et ``npc`` distinguent un PNJ (sans propriétaire), que seul le
    MJ lit.
    """

    id: UUID
    owner_id: UUID | None
    owner_name: str
    is_played: bool
    can_manage_notes: bool
    supernatural_level: int
    supernatural_name: str
    xp_general: ExperienceResponse
    xp_tactical: ExperienceResponse
    sheets: list[SheetResponse]
    expenses: list[ExpenseResponse]
    notes: list[NoteResponse]
    npc: NpcProfileResponse | None = None
    resources: list[ResourceResponse] = []


class AwakenedCharacterResponse(CharacterResponse):
    """Personnage éveillé vu par son joueur : les attributs vont jusqu'à 10."""

    awakened: Literal[True] = True


class GmCharacterResponse(CharacterResponse):
    """Personnage vu par le MJ, avec l'état de l'éveil."""

    awakened_at: datetime | None


AnyCharacterResponse = GmCharacterResponse | AwakenedCharacterResponse | CharacterResponse


def character_response(character: Character, viewer: Account) -> AnyCharacterResponse:
    """Projette un personnage selon ce que ``viewer`` a le droit d'en savoir."""
    fields = {
        "id": character.id,
        "owner_id": character.owner_id,
        "owner_name": character.owner_name,
        "is_played": character.is_played,
        "can_manage_notes": can_manage_notes(viewer, character.owner_id),
        "supernatural_level": character.supernatural_level,
        "supernatural_name": character.supernatural_name,
        "xp_general": ExperienceResponse(
            total=character.xp_general_total, balance=character.xp_balance(tactical=False)
        ),
        "xp_tactical": ExperienceResponse(
            total=character.xp_tactical_total, balance=character.xp_balance(tactical=True)
        ),
        "sheets": [SheetResponse.from_sheet(sheet) for sheet in character.sheets],
        "expenses": [
            ExpenseResponse(
                id=e.id,
                is_tactical=e.is_tactical,
                points=e.points,
                justification=e.justification,
                created_at=e.created_at,
            )
            for e in character.expenses
        ],
        "notes": [
            NoteResponse(id=n.id, title=n.title, body=n.body, updated_at=n.updated_at)
            for n in character.notes
        ],
        "npc": NpcProfileResponse.from_profile(character.npc) if character.npc else None,
        "resources": [ResourceResponse.from_resource(r) for r in character.resources],
    }
    if viewer.role is Role.GM:
        return GmCharacterResponse(**fields, awakened_at=character.awakened_at)
    if character.is_awakened:
        return AwakenedCharacterResponse(**fields)
    return CharacterResponse(**fields)


class CharacterListResponse(BaseModel):
    characters: list[AnyCharacterResponse]


class TacticListResponse(BaseModel):
    tactics: list[TacticResponse]


class NoteCreatedResponse(BaseModel):
    """Personnage à jour et identifiant de la note créée, à sélectionner."""

    character: AnyCharacterResponse
    note_id: UUID
