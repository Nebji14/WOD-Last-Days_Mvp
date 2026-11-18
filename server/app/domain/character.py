"""Modèle d'un personnage et de ses feuilles, et droits d'accès.

Un personnage est un personnage joueur (avec propriétaire) ou un PNJ du MJ
(sans propriétaire, avec un profil de PNJ).

Un personnage porte ce qui est commun à toutes ses formes (expérience, notes,
avantage surnaturel, éveil, ressources libres). Chaque forme est une feuille complète ; la forme
principale existe toujours.

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from app.domain.accounts import Account, Role
from app.domain.npc_profile import NpcProfile
from app.domain.resources import Resource


class EntryKind(StrEnum):
    """Type d'un élément de feuille (listes du verso)."""

    MERIT = "merit"
    FLAW = "flaw"
    POWER = "power"
    ITEM = "item"
    WEAPON = "weapon"
    ARMOR = "armor"


@dataclass(frozen=True, slots=True)
class Entry:
    """Atout, handicap, pouvoir, objet, arme ou armure.

    Les champs propres à un autre type que ``kind`` valent ``None``.
    ``roll`` porte la recette de jet d'un pouvoir, d'une arme ou d'un atout.
    """

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


@dataclass(frozen=True, slots=True)
class MoralityNote:
    """Annotation de moralité, liée au niveau où elle a été acquise."""

    id: UUID
    level: int
    body: str


@dataclass(frozen=True, slots=True)
class Tactic:
    """Tactique connue d'une feuille ; elle peut être partagée avec d'autres."""

    id: UUID
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class Expense:
    """Dépense d'expérience."""

    id: UUID
    is_tactical: bool
    points: int
    justification: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Note:
    """Note de la fiche (face NOTES)."""

    id: UUID
    title: str
    body: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Sheet:
    """Forme d'un personnage : une feuille complète.

    Attributs:
        texts: champs de texte (identité, description, protection globale).
        traits: valeurs des neuf attributs et des vingt-quatre compétences.
        numbers: valeurs effectives saisies, volonté disponible et
            moralité.
        specialties: spécialités par compétence, dans l'ordre de saisie.
    """

    id: UUID
    is_main: bool
    form_name: str
    texts: dict[str, str]
    traits: dict[str, int]
    numbers: dict[str, int]
    wound_track: str
    specialties: dict[str, list[str]]
    morality_notes: list[MoralityNote]
    entries: list[Entry]
    tactics: list[Tactic]


@dataclass(frozen=True, slots=True)
class Character:
    """Personnage joueur ou PNJ.

    Attributs:
        awakened_at: date de l'éveil, ``None`` s'il n'est pas déclenché. Secret
            du MJ : jamais transmis au joueur avant le déclenchement.
        owner_id: propriétaire du personnage joueur ; ``None`` pour un PNJ.
        is_played: personnage affiché sur le siège de son propriétaire.
        npc: profil du PNJ ; ``None`` pour un personnage joueur.
        sheets: formes du personnage, la principale en premier.
        resources: ressources libres (Mana, Douleur…), dans l'ordre de création.
    """

    id: UUID
    owner_id: UUID | None
    owner_name: str
    awakened_at: datetime | None
    supernatural_level: int
    supernatural_name: str
    xp_general_total: int
    xp_tactical_total: int
    is_played: bool
    sheets: list[Sheet]
    expenses: list[Expense]
    notes: list[Note]
    npc: NpcProfile | None = None
    resources: list[Resource] = field(default_factory=list)

    def resource(self, resource_id: UUID) -> Resource | None:
        """Retourne la ressource portant cet identifiant, ou ``None``."""
        return next((r for r in self.resources if r.id == resource_id), None)

    @property
    def is_npc(self) -> bool:
        """Feuille de PNJ : ni expérience, ni tactiques, ni formes, ni notes autonomes."""
        return self.npc is not None

    @property
    def is_awakened(self) -> bool:
        """L'éveil porte le plafond des attributs de 5 à 10."""
        return self.awakened_at is not None

    @property
    def main_sheet(self) -> Sheet:
        """Forme principale du personnage."""
        return next(sheet for sheet in self.sheets if sheet.is_main)

    def sheet(self, sheet_id: UUID) -> Sheet | None:
        """Retourne la forme portant cet identifiant, ou ``None``."""
        return next((sheet for sheet in self.sheets if sheet.id == sheet_id), None)

    def xp_spent(self, tactical: bool) -> int:
        """Total des dépenses d'un type d'expérience."""
        return sum(e.points for e in self.expenses if e.is_tactical is tactical)

    def xp_balance(self, tactical: bool) -> int:
        """Solde disponible : total acquis moins dépenses."""
        total = self.xp_tactical_total if tactical else self.xp_general_total
        return total - self.xp_spent(tactical)


@dataclass(frozen=True, slots=True)
class SeatCharacter:
    """Résumé public du personnage joué, affiché sur son siège à la table."""

    character_id: UUID
    name: str
    concept: str
    health_max: int
    wound_track: str
    willpower_max: int
    willpower_current: int


def can_read(actor: Account, owner_id: UUID | None) -> bool:
    """Le propriétaire et le MJ consultent la fiche.

    Un joueur n'ouvre jamais la fiche d'un autre joueur, ni celle d'un PNJ
    (``owner_id`` à ``None``), réservée au MJ.
    """
    return actor.role is Role.GM or (owner_id is not None and actor.id == owner_id)


def can_edit(actor: Account, owner_id: UUID | None) -> bool:
    """Le MJ modifie la fiche avec les mêmes possibilités que son propriétaire."""
    return can_read(actor, owner_id)


def can_manage_notes(actor: Account, owner_id: UUID | None) -> bool:
    """Seul le propriétaire crée, modifie et supprime ses notes ; le MJ les lit."""
    return actor.id == owner_id
